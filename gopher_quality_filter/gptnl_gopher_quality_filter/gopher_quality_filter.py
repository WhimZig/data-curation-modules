import numpy as np
from datatrove.data import Document
from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.pipeline.writers.disk_base import DiskWriter
from datatrove.utils.text import PUNCTUATION_SET
from loguru import logger


class GopherQualityFilter(BaseFilter):
    name = "🥇 Gopher Quality"
    _requires_dependencies = ["nltk", "langcodes"]

    def __init__(
        self,
        min_doc_words: int | None = 50,
        max_doc_words: int | None = 100000,
        min_avg_word_length: int | None = 2,
        max_avg_word_length: int | None = 10,
        max_symbol_word_ratio: float | None = 0.1,
        max_bullet_lines_ratio: float | None = 0.9,
        max_ellipsis_lines_ratio: float | None = 0.3,
        max_non_alpha_words_ratio: float | None = 0.8,
        min_stop_words: int | None = 2,
        stop_words: list[str] | None = None,
        exclusion_writer: DiskWriter = None,
        do_filter: bool = True,
    ):
        """Filter to apply Gopher's quality heuristic rules.

        Reference: https://arxiv.org/pdf/2112.11446.pdf

        Args:

          min_doc_words: Minimum number of words required in a document to be considered valid.
          max_doc_words: Maximum number of words allowed in a document to avoid overly long or noisy content.
          min_avg_word_length: Minimum average word length to filter out documents with overly short or fragmented words.
          max_avg_word_length: Maximum average word length to exclude documents with unnaturally long words.
          max_symbol_word_ratio: Maximum ratio of symbol-heavy words (e.g., containing punctuation or special characters).
          max_bullet_lines_ratio: Maximum ratio of lines starting with bullet characters (e.g., '-', '*') to avoid list-heavy documents.
          max_ellipsis_lines_ratio: Maximum ratio of lines containing ellipses (...) to filter out incomplete or trailing content.
          max_non_alpha_words_ratio: Maximum ratio of words containing non-alphabetic characters to reduce noisy or technical text.
          min_stop_words: Minimum number of stop words required to ensure the document contains natural language.
          stop_words: Optional list of stop words used to evaluate the naturalness of the document.
          exclusion_writer: Optional DiskWriter object to log excluded documents for auditing or debugging.
          do_filter: If True, applies the filtering rules and returns only the documents that pass all criteria.
        """

        super().__init__(exclusion_writer)
        self.min_doc_words = min_doc_words
        self.max_doc_words = max_doc_words
        self.min_avg_word_length = min_avg_word_length
        self.max_avg_word_length = max_avg_word_length
        self.max_symbol_word_ratio = max_symbol_word_ratio
        self.max_bullet_lines_ratio = max_bullet_lines_ratio
        self.max_ellipsis_lines_ratio = max_ellipsis_lines_ratio
        self.max_non_alpha_words_ratio = max_non_alpha_words_ratio
        self.min_stop_words = min_stop_words
        self.stop_words = stop_words
        self.do_filter = do_filter

    def filter(self, doc: Document) -> bool | tuple[bool, str]:
        """

        Args:
            doc: Applies the heuristics rules to decide if a document should be REMOVED

        Returns: False if sample.text does not pass any of the the heuristic tests
        """
        from langcodes import Language
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize

        detected_language = (
            Language.get(doc.metadata["language"]).language_name().lower()
        )
        text = doc.text

        try:
            words = word_tokenize(text, language=detected_language)
            lang_spec_stops_words_list = set(
                stopwords.words(detected_language)
                if self.stop_words is None
                else self.stop_words
            )
        except:
            logger.info("Tokenizer falling back to Dutch")
            words = word_tokenize(text, language="dutch")
            lang_spec_stops_words_list = set(
                stopwords.words("dutch") if self.stop_words is None else self.stop_words
            )

        n_words = len(words)

        non_symbol_words = [
            w for w in words if any(ch not in PUNCTUATION_SET for ch in w)
        ]
        n_non_symbol_words = len(non_symbol_words)

        # Define the necessary computation logic for each stat
        stats = {
            "n_non_symbol_words": lambda: n_non_symbol_words,
            "avg_word_length": lambda: np.mean([len(w) for w in non_symbol_words]),
            "hash_ratio": lambda: text.count("#") / n_words,
            "ellipsis_ratio": lambda: (text.count("...") + text.count("…")) / n_words,
            "bullet_lines_ratio": lambda: sum(
                s.lstrip().startswith("•") or s.lstrip().startswith("-")
                for s in text.splitlines()
            )
            / len(text.splitlines()),
            "ellipsis_lines_ratio": lambda: sum(
                s.rstrip().endswith("...") or s.rstrip().endswith("…")
                for s in text.splitlines()
            )
            / len(text.splitlines()),
            "alpha_words_ratio": lambda: sum(any(c.isalpha() for c in w) for w in words)
            / n_words,
            "stop_words_count": lambda: sum(
                w in lang_spec_stops_words_list for w in words
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
            self.min_doc_words
            and doc.metadata["n_non_symbol_words"] < self.min_doc_words
        ):
            return False, "gopher_short_doc"
        if (
            self.max_doc_words
            and doc.metadata["n_non_symbol_words"] > self.max_doc_words
        ):
            return False, "gopher_long_doc"

        if (
            self.min_avg_word_length
            and doc.metadata["avg_word_length"] < self.min_avg_word_length
        ):
            return False, "gopher_below_avg_threshold"
        if (
            self.max_avg_word_length
            and doc.metadata["avg_word_length"] > self.max_avg_word_length
        ):
            return False, "gopher_above_avg_threshold"

        if (
            self.max_symbol_word_ratio
            and doc.metadata["hash_ratio"] > self.max_symbol_word_ratio
        ):
            return False, "gopher_too_many_hashes"
        if (
            self.max_symbol_word_ratio
            and doc.metadata["ellipsis_ratio"] > self.max_symbol_word_ratio
        ):
            return False, "gopher_too_many_ellipsis"

        if (
            self.max_bullet_lines_ratio
            and doc.metadata["bullet_lines_ratio"] > self.max_bullet_lines_ratio
        ):
            return False, "gopher_too_many_bullets"
        if (
            self.max_ellipsis_lines_ratio
            and doc.metadata["ellipsis_lines_ratio"] > self.max_ellipsis_lines_ratio
        ):
            return False, "gopher_too_many_end_ellipsis"

        if (
            self.max_non_alpha_words_ratio
            and doc.metadata["alpha_words_ratio"] < self.max_non_alpha_words_ratio
        ):
            return False, "gopher_below_alpha_threshold"

        if (
            self.min_stop_words
            and doc.metadata["stop_words_count"] < self.min_stop_words
        ):
            return False, "gopher_enough_stop_words"

        return True
