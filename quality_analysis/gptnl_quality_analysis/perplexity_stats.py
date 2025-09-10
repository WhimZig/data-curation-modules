from pathlib import Path

import spacy
from datatrove.data import Document
from datatrove.io import DataFolderLike, cached_asset_path_or_download
from datatrove.pipeline.filters import LanguageFilter
from datatrove.pipeline.stats.base import BaseStats
from datatrove.pipeline.stats.config import DEFAULT_TOP_K_CONFIG, TopKConfig
from datatrove.utils.perplexity import KenlmModel, SentencePiece
from datatrove.utils.typeshelper import Languages
from huggingface_hub import hf_hub_url


class PerplexityStats(BaseStats):
    """
    Summary stats of perplexity metrics:

    Available stats:
    ccnet_perplexity_{model_dataset}_{language}
    """

    name = "🤯 Perplexity stats"
    _requires_dependencies = BaseStats._requires_dependencies + ["kenlm"]

    def __init__(
        self,
        output_folder: DataFolderLike,
        histogram_round_digits: int = 3,
        groups_to_compute: list = ["summary", "histogram"],
        top_k_config: TopKConfig = DEFAULT_TOP_K_CONFIG,
    ) -> None:
        super().__init__(
            output_folder, groups_to_compute, histogram_round_digits, top_k_config
        )

        self.models = {
            # IF wikipedia is the dataset and language is english, download the default version
            "english": KenlmModel(
                model_dataset="wikipedia", language=Languages.english
            ),
            # IF the dataset is kenlm_wikipedia_nl, download the model form BramVanroy
            "dutch": TNO_KenlmModel(model_dataset="wiki_nl_pos", language="nl"),
        }

    def extract_stats(self, doc: Document) -> dict[str, int | float]:
        from langcodes import Language

        detected_language = (
            Language.get(doc.metadata.get("language", "")).language_name().lower()
            if "language" in doc.metadata
            else Language.get(LanguageFilter().model.predict(doc=doc)[0][0])
            .language_name()
            .lower()
        )

        if detected_language in self.models:
            return {
                f"perplexity_{detected_language}": self.models[
                    detected_language
                ].get_perplexity(doc.text)
            }
        else:
            return {
                f"perplexity_{'dutch'}": self.models["dutch"].get_perplexity(doc.text)
            }


class TNO_KenlmModel(KenlmModel):
    """A custom Kenlm model class that allows loading models from external repositories,
    including models from BramVanRoy, in addition to the official repository.
    """

    def __init__(self, model_dataset: str, language: str):
        """Initialize the TNO_KenlmModel with a specified dataset and language.

        Args:
            model_dataset (str): The name of the dataset to be used.
            language (str): The language code for the model.
        """
        super().__init__(model_dataset, language)
        self.model_repo = "BramVanroy/kenlm_wikipedia_nl"

    @property
    def model(self):
        """Load the Kenlm model from the specified dataset.

        This property checks if the model is already loaded. If not, it attempts to load
        the model from a predefined repository mapping based on the dataset name.

        Returns:
            kenlm.Model: The loaded Kenlm model.
        """
        import kenlm

        model_path = Path(f"{self.model_dataset}.arpa.bin")
        # Download the model if not already cached
        path = cached_asset_path_or_download(
            hf_hub_url(self.model_repo, str(model_path))
        )
        self._model = kenlm.Model(path)

        return self._model

    @property
    def tokenizer(self):
        """Get the tokenizer for the model.

        This property initializes the tokenizer if it hasn't been created yet.

        Returns:
            TNO_SentencePiece: The tokenizer associated with the model.
        """
        if self._tokenizer is None:
            # Initialize the tokenizer with the dataset and language
            self._tokenizer = TNO_SentencePiece(self.model_dataset, self.language)
        return self._tokenizer


class TNO_SentencePiece(SentencePiece):
    """A custom SentencePiece tokenizer that supports loading models from both
    the official HuggingFace repository and the BramVanRoy repository.
    """

    def __init__(self, model_dataset: str, model_name: str):
        """Initialize the TNO_SentencePiece with a specified dataset and model name.

        Args:
            model_dataset (str): The name of the dataset to be used.
            model_name (str): The name of the model to be loaded.
        """
        super().__init__(model_dataset, model_name)

    @property
    def model(self):
        """Load the appropriate SentencePiece model based on the dataset.

        This property checks if the model is already loaded. If not, it loads the model
        using the corresponding loader function based on the dataset name.

        Returns:
            sentencepiece.SentencePieceProcessor: The loaded SentencePiece model.
        """
        if self._model is None:
            # Mapping of dataset names to their respective model loading functions
            self._model = spacy.load("nl_core_news_sm")
        return self._model

    def tokenize(self, text: dict) -> dict:
        """Tokenize the input text using the loaded SentencePiece model.

        Args:
            text (dict): The input text to be tokenized.

        Returns:
            dict: The tokenized output as a string of space-separated tokens.
        """

        # Tokenize using spaCy and return the part-of-speech tags
        return " ".join([token.pos_ for token in self.model(text)])
