import numpy as np
from datatrove.data import Document
from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.pipeline.writers.disk_base import DiskWriter
from langcodes import Language
from loguru import logger
from nltk.tokenize import word_tokenize


class NordicPileQualityFilter(BaseFilter):
    name = "❄️ NordicPile Quality"
    _requires_dependencies = ["nltk", "langcodes"]

    def __init__(
        self,
        max_digit_fraction: float | None = 0.2,
        min_n_char: float | None = 50,
        min_mean_med_char: float | None = 9,
        min_mean_med_word: float | None = 2.1,
        exclusion_writer: DiskWriter = None,
        do_filter: bool = True,
    ):
        """Filter to apply NordicPile's quality heuristic rules.
        Only contains the missing filters that are not in the GopherQualityFilter such as the digit_fraction, document length and mean line length

        Reference: https://arxiv.org/pdf/2303.17183

        Args:

            max_digit_fraction: Max number of digits fraction in the text
            min_n_char: Min of characters in a text
            min_mean_med_char: Minimum mean_med of char in non empty lines
            min_mean_med_word: Minimum mean_med of words in non empty lines
            exclusion_writer:
            do_filter: If true does perform filtering (a new dataset will be created with only the datapoints that passed the filtering)

        """
        super().__init__(exclusion_writer)
        self.max_digit_fraction = max_digit_fraction
        self.min_n_char = min_n_char
        self.min_mean_med_char = min_mean_med_char
        self.min_mean_med_words = min_mean_med_word
        self.do_filter = do_filter

    def filter(self, doc: Document) -> bool | tuple[bool, str]:
        """

        Args:
            doc: Applies the heuristics rules to decide if a document should be REMOVED

        Returns: False if sample.text does not pass any of the the heuristic tests
        """

        text = doc.text

        if len(text) == 0:
            return False, "empty_text"

        detected_language = (
            Language.get(doc.metadata["language"]).language_name().lower()
        )

        # Define the necessary computation logic for each stat
        mean_med = lambda values: (np.mean(values) + np.median(values)) / 2

        stats = {
            "digit_char_ratio": lambda: sum(c.isdigit() for c in text.strip())
            / len(text.strip()),
            "n_char": lambda: len("".join(text.split())),
            "mean_med_char": lambda: mean_med(
                [
                    len("".join(line.split()))
                    for line in text.splitlines()
                    if line.strip()
                ]
            ),
            "mean_med_word": lambda: mean_med(
                [
                    len(
                        self.get_word_tokenize(
                            line, detected_language=detected_language
                        )
                    )
                    for line in text.splitlines()
                    if line.strip()
                ]
            ),
        }

        # Compute or retrieve each stat from metadata
        for stat_name, compute_stat in stats.items():
            if stat_name not in doc.metadata:
                doc.metadata[stat_name] = compute_stat()

        if not self.do_filter:
            return True

        # Start filtering based on the computed stats
        if (
            self.max_digit_fraction
            and doc.metadata["digit_char_ratio"] > self.max_digit_fraction
        ):
            return False, "nordicpile_digit_fraction"

        if self.min_n_char and doc.metadata["n_char"] < self.min_n_char:
            return False, "nordicpile_short_doc"

        if (
            self.min_mean_med_char
            and doc.metadata["mean_med_char"] < self.min_mean_med_char
        ):
            return False, "nordicpile_mean_med_char"

        if (
            self.min_mean_med_words
            and doc.metadata["mean_med_word"] < self.min_mean_med_words
        ):
            return False, "nordicpile_mean_med_word"

        return True

    def get_word_tokenize(self, text: str, detected_language: str) -> list[str]:
        """Tokenize the string depending on its language."""
        try:
            words = word_tokenize(text, language=detected_language)
        except:
            logger.info("Tokenizer falling back to Dutch")
            words = word_tokenize(text, language="dutch")
        return words
