from abc import abstractmethod
from collections import defaultdict
from collections.abc import Callable

import flair
import torch
from flair.data import Sentence

from .informed_formatter import (
    InformedFormatter,
    adjust_indices,
    calculate_offsets,
    split_text_into_chunks,
)
from .name_grouping import assign_grouped_entity_masks


class NERFormatter(InformedFormatter):
    """Handles Named Entity Recognition formatting by replacing specified entities with a given mask.

    Args:
        entity_types (str | list[str]): Types of entities to identify and replace.
        mask (str, optional): Replacement text for entities. Defaults to None.
        validator (Callable[[str], bool], optional): Function to validate entities before replacement. Defaults to None.
        **kwargs: Additional keyword arguments to store as instance attributes.
    """

    model_name = "NER-model-not-specified"

    def __init__(
        self,
        entity_types: str | list[str],
        mask: str | list[str] | None = None,
        validator: Callable[[str], bool] | None = None,
        group: bool = False,
        **kwargs,
    ):
        super().__init__()
        if isinstance(entity_types, str):
            entity_types = [entity_types]
        elif not isinstance(entity_types, list):
            raise ValueError("entity_types must be a string or a list of strings.")

        self.entity_types = entity_types
        self.entity_masks = [mask] if isinstance(mask, str) else mask
        self.validator = validator
        self.remove_example = True
        self.supported_languages = []
        self.device = None
        self.group = group

        for key, value in kwargs.items():
            setattr(self, key, value)

    def replace_substring(
        self,
        original_string: str,
        start_index: int,
        end_index: int,
        label: str | None = None,
    ) -> str:
        """Replaces a substring in the original string with a label.

        Args:
            original_string (str): The original text.
            start_index (int): Start index of the substring to replace.
            end_index (int): End index of the substring to replace.
            label (str): The replacement text.

        Returns:
            str: Modified string with the specified substring replaced.

        Raises:
            ValueError: If the provided indices are invalid.
        """
        if start_index < 0:
            raise ValueError(
                f"Start index {start_index} is out of bounds; it cannot be negative."
            )
        if end_index > len(original_string):
            raise ValueError(
                f"End index {end_index} is out of bounds; it exceeds the length of the string."
            )
        if start_index > end_index:
            raise ValueError(
                f"Start index {start_index} cannot be greater than end index {end_index}."
            )

        modified_string = (
            original_string[:start_index] + label + original_string[end_index:]
        )
        return modified_string

    def to_device(self) -> torch.device:
        """Determines which device (CPU or GPU) to use for processing.

        Returns:
            torch.device: The selected device for computation.
        """
        if torch.cuda.is_available():
            # Initialize variables to track the best GPU
            best_gpu = None
            max_free_memory = 0

            # Iterate over each GPU to find the one with the most available memory
            for i in range(torch.cuda.device_count()):
                free_memory, _ = torch.cuda.mem_get_info(i)
                if free_memory > max_free_memory:
                    max_free_memory = free_memory
                    best_gpu = i

            # Choose the GPU with the most free memory
            device = (
                torch.device(f"cuda:{best_gpu}")
                if best_gpu is not None
                else torch.device("cpu")
            )
        else:
            device = torch.device("cpu")

        return device

    def replace_entities(
        self, text: str, entities: list[dict], language: str = "unknown"
    ) -> tuple[str, dict]:
        metadata = {
            "entity_types": self.entity_types,
            "entity_type_counts": [0 for _ in self.entity_types],
            "masks": [],
            "mask_counts": [],
        }
        if len(entities) == 0:
            return text, metadata

        not_removed_entities = []
        not_removed_entities_type = []
        if self.validator:
            new_entities = []
            for entity in entities:
                if self.validator(entity["text"]):
                    new_entities.append(entity)
                else:
                    not_removed_entities.append(entity["text"])
                    not_removed_entities_type.append(entity["label"])
            entities = new_entities

        if self.group:
            entities = assign_grouped_entity_masks(
                entities, self.entity_types, self.entity_masks
            )
        elif self.entity_masks:
            if isinstance(self.entity_masks, str):
                for entity in entities:
                    entity["mask"] = self.entity_masks
            elif isinstance(self.entity_masks, list):
                for entity in entities:
                    entity["mask"] = self.entity_masks[
                        self.entity_types.index(entity["label"])
                    ]
        else:
            for entity in entities:
                entity["mask"] = f"<{entity['label'].replace(' ', '_')}>"

        mask_countsdict = defaultdict(int)
        entity_countsdict = {entity_type: 0 for entity_type in self.entity_types}
        for entity in reversed(entities):
            mask_countsdict[entity["mask"]] += 1
            entity_countsdict[entity["label"]] += 1
            text = self.replace_substring(
                text, entity["start"], entity["end"], entity["mask"]
            )

        metadata["masks"] = [mask for mask, _ in mask_countsdict.items()]
        metadata["mask_counts"] = [count for _, count in mask_countsdict.items()]
        metadata["entity_type_counts"] = [
            count for _, count in entity_countsdict.items()
        ]
        metadata["not_removed_entities"] = not_removed_entities
        metadata["not_removed_entities_type"] = not_removed_entities_type

        return text, metadata

    def predict_entities_from_long_text(
        self,
        text: str,
        language: str,
        max_chunk_length: int = 5000,
        batch_size: int = 32,
    ) -> list[dict]:
        if max_chunk_length <= 0:
            raise ValueError("chunk_size must be greater than 0")

        def batches(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i : i + n]

        chunks = split_text_into_chunks(text, max_chunk_length)
        offsets = calculate_offsets(chunks)

        all_entities = []
        chunk_entities_list = []
        for chucks_batch in batches(chunks, min(batch_size, len(chunks))):
            chunk_entities_list.extend(
                self.batch_predict_entities(chucks_batch, language)
            )

        for chunk_entities, offset in zip(chunk_entities_list, offsets, strict=False):
            adjusted_entities = adjust_indices(chunk_entities, offset)
            all_entities.extend(adjusted_entities)

        return all_entities

    def check_language_and_device(self, language: str):
        if language not in self.supported_languages:
            print(
                f'Unsupported language: "{language}", not in {self.supported_languages}. Defaulting to "nl".'
            )
            language = "nl"

        if self.device is None:
            self.device = self.to_device()

        return language

    def format(
        self, text: str, language: str = "unknown", with_metadata=False
    ) -> str | tuple[str, dict]:
        if self.remove_example:
            language = self.check_language_and_device(language)
            text, metadata = self.format_ner(text, language)
        if not with_metadata:
            return text
        return text, metadata

    @abstractmethod
    def batch_predict_entities(self, chunks: list[str], language: str):
        raise NotImplementedError()

    @abstractmethod
    def format_ner(self, text: str, language: str) -> tuple[str, dict]:
        """Replaces entities in the text with a mask using the specified model.

        Args:
            text (str): The text to be processed.
            language (str): The language of the text for model selection.

        Returns:
            tuple[str, dict]: A tuple containing the text with entities replaced by masks and associated metadata.

        Raises:
            NotImplementedError: This method should be implemented by subclasses.
        """
        raise NotImplementedError()


class PII_Flair_Large_Formatter(NERFormatter):
    """Formats text to replace named entities using a FLAIR transformer model.

    Attributes:
        model_name (str): The base model name template with placeholders for different languages.
        flair_taggers (dict): Cached FLAIR SequenceTagger models for specified languages.
    """

    model_name = "flair/ner-<language>-large"

    def __init__(self, **kwargs):
        """Initializes the PII_Flair_Large_Formatter with specified attributes.

        Args:
            **kwargs: Additional keyword arguments passed to the NERFormatter.
        """
        super().__init__(**kwargs)
        self.flair_taggers = None
        self.language_mapper = {"nl": "dutch", "en": "english"}

    def batch_predict_entities(self, chunks: list[str], language: str) -> list[dict]:
        chunks = [Sentence(chunk) for chunk in chunks]
        self.flair_taggers[language].predict(chunks)
        chunk_entities = []
        for chunk in chunks:
            entities = []
            for entity in chunk.get_spans("ner"):
                if entity.tag in self.entity_types:
                    entities.append(
                        {
                            "start": entity.start_position,
                            "end": entity.end_position,
                            "text": entity.text,
                            "label": entity.tag,
                            "score": entity.score,
                        }
                    )
            chunk_entities.append(entities)
        return chunk_entities

    def format_ner(self, text: str, language: str) -> tuple[str, dict]:
        """Replaces entities in the text with a mask using the FLAIR model.

        Args:
            text (str): The text to be processed.
            language (str): The language of the text for model selection.

        Returns:
            str: The text with specified entities replaced by masks.
            dict: Metadata about the formatting process.
        """
        if self.flair_taggers is None:
            self.flair_taggers = {}

        if language not in self.flair_taggers:
            from flair.models import SequenceTagger

            self.flair_taggers[language] = SequenceTagger.load(
                self.model_name.replace("<language>", self.language_mapper[language])
            )
            self.flair_taggers[language].to(self.device)
            flair.device = self.device

        entities = self.predict_entities_from_long_text(text, language)
        return super().replace_entities(text, entities, language)


class PII_GLiNERFormatter(NERFormatter):
    """Formatter using the GLiNER model for Named Entity Recognition.

    This formatter uses the GLiNER model to identify and replace entities in multiple languages.

    Attributes:
        model_name (str): The model identifier for the GLiNER multi-domain PII model.
        gliner (GLiNER): The GLiNER model instance for entity recognition.
    """

    model_name = "E3-JSI/gliner-multi-pii-domains-v1"

    def __init__(self, **kwargs):
        """Initializes PII_GLiNERFormatter with the necessary attributes.

        Args:
            **kwargs: Additional keyword arguments for initializing the NERFormatter.
        """
        super().__init__(**kwargs)
        self.gliner = None

    def batch_predict_entities(self, chunks: list[str], language: str):
        return self.gliner.batch_predict_entities(
            texts=chunks, labels=self.entity_types
        )

    def format_ner(self, text: str, language: str) -> tuple[str, dict]:
        """Replaces entities in the text with a mask using the GLiNER model.

        Args:
            text (str): The text to be processed.
            language (str): The language of the text for model selection.

        Returns:
            str: The text with specified entities replaced by masks.
            dict: metadata about the formatting process.
        """
        if self.gliner is None:
            from gliner import GLiNER

            self.gliner = GLiNER.from_pretrained(self.model_name)
            self.gliner.to(self.device)

        entities = self.predict_entities_from_long_text(
            text, language, max_chunk_length=384
        )
        return super().replace_entities(text, entities, language)


class HuggingFaceNERFormatter(NERFormatter):
    def __init__(self, **kwargs):
        """Initializes the formatter with the specified kwargs.

        Args:
            **kwargs: Additional keyword arguments for NERFormatter.
        """
        super().__init__(**kwargs)
        self.tokenizer, self.model, self.pipeline = None, None, None
        self.space_replacer = ""

    def batch_predict_entities(self, chucks: list[str], language: str):
        batch_raw_entities = self.pipeline(chucks)
        return [
            self.format_entities(raw_entities) for raw_entities in batch_raw_entities
        ]

    def format_entities(self, raw_entities):
        formatted_entities = []
        current_entity = None

        for entity in raw_entities:
            ent_type = entity["entity"]
            ent_score = entity["score"]
            start_index = entity["start"]
            end_index = entity["end"]
            word = entity["word"]

            base_label = ent_type.split("-")[-1]
            if base_label not in self.entity_types:
                continue

            if current_entity and (
                current_entity["end"] == start_index or ent_type.startswith("I-")
            ):
                clean_word = word.replace(self.space_replacer, " ")
                current_entity["end"] = end_index
                current_entity["text"] += clean_word
                current_entity["score"] = max(current_entity["score"], ent_score)
            elif ent_type.startswith("B-"):
                if current_entity:
                    formatted_entities.append(current_entity)
                clean_word = word.replace(self.space_replacer, "")
                current_entity = {
                    "start": start_index,
                    "end": end_index,
                    "text": clean_word,
                    "label": base_label,
                    "score": ent_score,
                }

        if current_entity:
            formatted_entities.append(current_entity)
        return formatted_entities

    def format_ner(self, text: str, language: str) -> tuple[str, dict]:
        entities = self.predict_entities_from_long_text(text, language)
        return super().replace_entities(text, entities, language)


class PII_RobBERT_V2_Dutch_Formatter(HuggingFaceNERFormatter):
    """Formatter for named entity recognition using the RobBERT V2 model.

    This class utilizes the RobBERT V2 model to identify and mask specific
    entities in Dutch text as per specified types.

    Attributes:
        model_name (str): Identifier for the RobBERT V2 NER model.
    """

    model_name = "pdelobelle/robbert-v2-dutch-ner"

    def __init__(self, **kwargs):
        """Initializes the formatter with the specified keyword arguments.

        Args:
            **kwargs: Additional keyword arguments passed to the NERFormatter.
        """
        super().__init__(**kwargs)
        self.tokenizer, self.model = None, None
        self.space_replacer = "Ġ"

    def format_ner(self, text: str, language: str) -> tuple[str, dict]:
        """Formats the input text by replacing recognized entities with masks.

        Args:
            text (str): The text to be processed.
            language (str): Language of the text. Defaults to 'dutch'.

        Returns:
            str: Text with specified entities replaced by masks.

        Raises:
            AssertionError: If an unsupported language is specified.
        """
        if self.model is None:
            from transformers import (
                AutoModelForTokenClassification,
                AutoTokenizer,
                pipeline,
            )

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(
                self.model_name
            )
            self.pipeline = pipeline(
                "ner", model=self.model, tokenizer=self.tokenizer, device=self.device
            )

        entities = self.predict_entities_from_long_text(
            text, language, max_chunk_length=500
        )
        return super().replace_entities(text, entities, language)


class PII_XLM_RoBERTa_Dutch_Formatter(HuggingFaceNERFormatter):
    """Formats text by replacing named entities using XLM-RoBERTa model.

    This formatter utilizes the XLM-RoBERTa model finetuned for Dutch
    to identify and mask specified entity types in text.

    Attributes:
        model_name (str): Identifier for the XLM-RoBERTa model.
    """

    model_name = "xlm-roberta-large-finetuned-conll02-dutch"

    def __init__(self, **kwargs):
        """Initializes the formatter with the specified kwargs.

        Args:
            **kwargs: Additional keyword arguments for NERFormatter.
        """
        super().__init__(**kwargs)
        self.space_replacer = "▁"

    def format_ner(self, text: str, language: str) -> tuple[str, dict]:
        """Formats the input text by masking recognized entities.

        Args:
            text (str): Text to process for entity masking.
            language (str): Language of the text.

        Returns:
            str: Text with specified entities replaced by masks.
            dict: Dictionary with metadata.
        """
        if self.model is None:
            from transformers import (
                AutoModelForTokenClassification,
                AutoTokenizer,
                pipeline,
            )

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(
                self.model_name
            )
            self.pipeline = pipeline(
                "ner", model=self.model, tokenizer=self.tokenizer, device=self.device
            )

        return super().format_ner(text, language)


def pii_ner_formatter_class_factory(class_=None, **kwargs) -> NERFormatter:
    # Also requires name argument in factory function which seemed unnecessary.
    # Define the new class dynamically
    """Creates a new NERFormatter class dynamically.

    This factory function generates a new class that inherits from the given
    class_, including additional attributes specified in kwargs.

    Args:
        class_ (type): The base class to inherit from, expected to be a subclass of NERFormatter.
        **kwargs: Additional attributes to include in the new class and passed
            to the constructor during initialization.

    Returns:
        type: A dynamically created subclass of the given class_ with added attributes.
    """
    new_class = type(
        class_.__name__,
        (class_,),  # Inherit from PII_NERFormatter
        {
            "name": class_.__name__,
            "__init__": lambda self: super(type(self), self).__init__(**kwargs),
            **kwargs,
            **kwargs,
        },
    )
    return new_class
