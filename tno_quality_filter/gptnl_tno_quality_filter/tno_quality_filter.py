import numpy as np
from datatrove.data import Document
from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.pipeline.writers.disk_base import DiskWriter


class TnoQualityFilter(BaseFilter):
    name = "🦸 TNO Quality"
    _requires_dependencies = ["nltk"]

    def __init__(
        self,
        min_line_length: int | None = 10,
        max_line_length: int | None = 10000,
        min_avg_line_length: int | None = 10,
        max_avg_line_length: int | None = 5000,
        exclusion_writer: DiskWriter = None,
        do_filter: bool = True,
    ):
        """Filter to apply quality heuristic rules from DataJuicer.

                Reference:
                https://github.com/modelscope/data-juicer/tree/main


        Args:
            min_line_length: Minimum number of characters required in a line to be considered valid.
            max_line_length: Maximum number of characters allowed in a line to avoid excessively long or noisy lines.
            min_avg_line_length: Minimum average line length across the document to ensure sufficient content density.
            max_avg_line_length: Maximum average line length to exclude documents with overly verbose or unnatural formatting.
            exclusion_writer: Optional DiskWriter object to log excluded documents for auditing or debugging purposes.
            do_filter: If True, applies the filtering rules and returns only the documents that pass all criteria.
        """

        super().__init__(exclusion_writer)
        self.min_line_length = min_line_length
        self.max_line_length = max_line_length
        self.min_avg_line_length = min_avg_line_length
        self.max_avg_line_length = max_avg_line_length
        self.do_filter = do_filter

    def filter(self, doc: Document) -> bool | tuple[bool, str]:
        """

        Args:
            doc: Applies the heuristics rules to decide if a document should be REMOVED

        Returns: False if sample.text does not pass any of the the heuristic tests
        """
        text = doc.text
        lines = text.splitlines()
        line_lengths = list(map(len, lines))

        # Compute statistics
        stats = {
            "line_length": lambda: max(line_lengths) if line_lengths else 0,
            "avg_line_length": lambda: (
                np.median(line_lengths) if len(line_lengths) != 0 else 0.0
            ),
        }

        # Compute or retrieve each stat from metadata
        for stat_name, compute_stat in stats.items():
            if stat_name not in doc.metadata:
                doc.metadata[stat_name] = compute_stat()

        # Retrieve statistics from metadata
        line_length = doc.metadata["line_length"]
        avg_line_length = doc.metadata["avg_line_length"]

        # Check conditions based on statistics
        checks = [
            (
                self.min_line_length and line_length < self.min_line_length,
                "tno_min_line_length",
            ),
            (
                self.max_line_length and line_length > self.max_line_length,
                "tno_max_line_length",
            ),
            (
                self.min_avg_line_length and avg_line_length < self.min_avg_line_length,
                "tno_avg_line_length",
            ),
            (
                self.max_avg_line_length and avg_line_length > self.max_avg_line_length,
                "tno_avg_line_length",
            ),
        ]

        if not self.do_filter:
            return True

        for condition, message in checks:
            if condition:
                return False, message

        return True
