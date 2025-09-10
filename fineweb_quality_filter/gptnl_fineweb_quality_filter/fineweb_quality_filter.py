from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.pipeline.filters.gopher_repetition_filter import find_duplicates
from datatrove.pipeline.writers.disk_base import DiskWriter


class FineWebQualityFilter(BaseFilter):
    name = "🍷 FineWeb Quality"
    _requires_dependencies = ["nltk", "langcodes"]

    def __init__(
        self,
        exclusion_writer: DiskWriter = None,
        line_punct_thr: float = 0.12,
        line_punct_exclude_zero: bool = False,
        short_line_thr: float = 0.67,
        short_line_length: int = 30,
        char_duplicates_ratio: float = 0.01,
        new_line_ratio: float = 0.3,
        do_filter: bool = True,
    ):
        """
        Initializes the text filtering class with configurable heuristic parameters.

        Args:
            exclusion_writer (DiskWriter | None): Optional writer to log excluded lines or pages.
            line_punct_thr (float): Threshold ratio of lines ending with terminal punctuation.
            line_punct_exclude_zero (bool): Whether to exclude pages with zero terminal punctuation lines.
            stop_chars (tuple[str, ...] | None): Characters considered as terminal punctuation (e.g., '.', '?', '!').
            short_line_thr (float): Threshold ratio of short lines to total lines for exclusion.
            short_line_length (int): Maximum character length for a line to be considered short.
            char_duplicates_ratio (float): Maximum allowed ratio of duplicated characters in a line.
            new_line_ratio (float): Minimum ratio of newline characters required in a page.
            language (str): Language used for filtering logic, defaults to English.
        """

        super().__init__(exclusion_writer)
        self.line_punct_thr = line_punct_thr
        self.line_punct_exclude_zero = line_punct_exclude_zero
        self.short_line_threshold = short_line_thr
        self.short_line_length = short_line_length
        self.char_duplicates_ratio = char_duplicates_ratio
        self.new_line_ratio = new_line_ratio
        self.do_filter = do_filter

    def filter(self, doc) -> bool | tuple[bool, str]:
        from langcodes import Language
        from nltk import word_tokenize

        # Define the necessary computation logic for each stat
        stop_chars = (".", "'", '"', "!", "?")
        lines = doc.text.split("\n")
        non_empty_lines = [line for line in lines if line.strip() != ""]
        detected_language = (
            Language.get(doc.metadata["language"]).language_name().lower()
        )

        stats = {
            "line_punct_ratio": lambda: sum(
                1 for line in lines if line.endswith(stop_chars)
            )
            / len(lines),
            "short_line_ratio": lambda: sum(
                1 for line in lines if len(line) <= self.short_line_length
            )
            / len(lines),
            "char_dup_ratio": lambda: find_duplicates(non_empty_lines)[1]
            / len(doc.text.replace("\n", "")),
            "list_ratio": lambda: doc.text.count("\n")
            / len(word_tokenize(doc.text, language=detected_language)),
        }

        # Compute or retrieve each stat from metadata
        for stat_name, compute_stat in stats.items():
            if stat_name not in doc.metadata:
                doc.metadata[stat_name] = compute_stat()

        if not self.do_filter:
            return True
        # Start filtering based on the computed stats
        if doc.metadata["line_punct_ratio"] <= self.line_punct_thr and not (
            doc.metadata["line_punct_ratio"] == 0 and self.line_punct_exclude_zero
        ):
            return False, "line_punct_ratio"

        if doc.metadata["short_line_ratio"] >= self.short_line_threshold:
            return False, "short_line_ratio"

        if doc.metadata["char_dup_ratio"] >= self.char_duplicates_ratio:
            return False, "char_dup_ratio"

        if doc.metadata["list_ratio"] > self.new_line_ratio:
            return False, "list_ratio"

        return True
