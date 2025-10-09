import torch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer, pipeline

from .informed_formatter import InformedFormatter


def split_text_into_chunks(
    text: str, max_chunk_length: int, lang: str
) -> list[tuple[str, int]]:
    """Splits the text into chunks based on the specified split type and records the starting index of each chunk.

    Args:
        text (str): The input text to split.
        max_chunk_length (int): The maximum length of each chunk.
        lang (str): Language of the text in order to use the right tokenizer of the right toxic language model

    Returns:
        list[tuple[str, int]]: A list of tuples where each tuple contains a text chunk and its starting index.
    """

    if lang == "nl":
        tokenizer = AutoTokenizer.from_pretrained("GroNLP/bert-base-dutch-cased")
    elif lang == "en":
        tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    # Define a custom length function
    def custom_length_function(text):
        return len(tokenizer.encode(text))

    # Initialize the text splitter with the custom length function
    text_splitter = RecursiveCharacterTextSplitter(
        length_function=custom_length_function,
        chunk_size=max_chunk_length,
        chunk_overlap=0,
    )

    # Split the text into chunks and track start indices
    def split_text_with_indices(text_splitter, text):
        chunks = text_splitter.split_text(text)
        result = []
        current_index = 0
        for chunk in chunks:
            result.append((chunk, current_index))
            current_index += len(chunk)
        return result

    # Split the text and get chunks with indices
    return split_text_with_indices(text_splitter, text)


class ToxicLanguageDetection(InformedFormatter):
    """Applies toxic language detection.

    Based on `GroNLP/bert_dutch_base_offensive_language` and `tomh/toxigen_hatebert`.
    """

    name = "🚫 ToxicLanguageDetection"
    _requires_dependencies = ["transformers", "langcodes", "nltk"]

    def __init__(self, threshold=0.0, max_chunk_length=512):
        """Filter to apply toxic language detection.

        Args:
            threshold: The threshold above which a chunk is considered toxic. Defaults to 0.0.
            max_chunk_length: Maximum length of a chunk to process at once. Defaults to 512.
        """
        super().__init__()
        self.device = None
        self.threshold = threshold
        self.max_chunk_length = max_chunk_length
        self.dutch_hate_pipe = None
        self.english_hate_pipe = None
        self.supported_languages = ["nl", "en"]
        self.nltk_language_map = {
            "nl": "dutch",
            "en": "english",
        }
        self.model_label_map = {
            "nl": {
                "LABEL_0": "Acceptable",
                "LABEL_1": "Inappropriate",
                "LABEL_2": "Offensive",
                "LABEL_3": "Violent",
            },
            "en": {"LABEL_0": "Acceptable", "LABEL_1": "Toxic"},
        }

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
                try:
                    free_memory, _ = torch.cuda.mem_get_info(i)
                except AttributeError:
                    # If mem_get_info is not available, skip memory tracking
                    free_memory = 0
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

    def format(
        self, text: str, language: str = "nl", with_metadata: bool = False
    ) -> tuple[str, list[dict]]:
        """Detects and removes toxic language from the text.

        Args:
            text (str): The input text to process.
            language (str): The language of the text ('nl' for Dutch, 'en' for English).
            with_metadata (bool): If True, returns metadata about removed toxic sentences.

        Returns:
            tuple[str, list[dict]]: A tuple containing the formatted text and a list of metadata dictionaries.
        """
        if language not in self.supported_languages:
            # logger.debug(
            #     f'Unsupported language: "{language}", not in {self.supported_languages}. Defaulting to "nl".'
            # )
            return text, []

        if not self.device:
            self.device = self.to_device()

        # Split text into chunks along with their starting indices
        chunks_with_index = split_text_into_chunks(
            text,
            max_chunk_length=self.max_chunk_length,
            lang=language,
        )

        # Extract only the text chunks for processing
        chunks = [chunk for chunk, _ in chunks_with_index]

        # Initialize the appropriate hate speech detection pipeline
        if language == "nl":
            if not self.dutch_hate_pipe:
                self.dutch_hate_pipe = pipeline(
                    "text-classification",
                    model="IMSyPP/hate_speech_nl",
                    device=self.device,
                    tokenizer="GroNLP/bert-base-dutch-cased",
                )  # highest recall
            predictions = self.dutch_hate_pipe(chunks)
        elif language == "en":
            if not self.english_hate_pipe:
                self.english_hate_pipe = pipeline(
                    "text-classification",
                    model="tomh/toxigen_hatebert",
                    tokenizer="bert-base-uncased",
                    device=self.device,
                )
            predictions = self.english_hate_pipe(chunks)

        # Map the model's labels to human-readable labels
        for prediction in predictions:
            label = prediction["label"]
            prediction["explainable_label"] = self.model_label_map[language].get(
                label, "Unknown"
            )

        if len(chunks) != len(predictions):
            raise ValueError("`text` and `predictions` must be the same length")

        # Combine chunks with their predictions and starting indices
        zipped_chunks_predictions = list(
            zip(chunks_with_index, predictions, strict=False)
        )

        # Build the formatted text by excluding toxic chunks
        formatted_chunks = []
        for (chunk, _), prediction in zipped_chunks_predictions:
            if not (
                prediction["label"] != "LABEL_0"
                and float(prediction["score"]) > self.threshold
            ):
                formatted_chunks.append(chunk)
        formatted_text = " ".join(formatted_chunks)

        if not with_metadata:
            return formatted_text, []

        # Collect metadata for toxic chunks
        toxic_sentences = []
        for (chunk, start_idx), prediction in zipped_chunks_predictions:
            if (
                prediction["label"] != "LABEL_0"
                and float(prediction["score"]) > self.threshold
            ):
                toxic_sentences.append(
                    {
                        "sentence": chunk,
                        "start_index": start_idx,
                        "label": prediction["explainable_label"],
                        "score": prediction["score"],
                    }
                )

        return formatted_text, toxic_sentences
