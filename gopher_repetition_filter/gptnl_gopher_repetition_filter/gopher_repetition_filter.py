import re
from collections import Counter

from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.pipeline.writers.disk_base import DiskWriter
from loguru import logger

"""
Table A1 from https://arxiv.org/pdf/2112.11446.pdf
    duplicate line fraction                 0.30
    duplicate paragraph fraction            0.30
    duplicate line character fraction       0.20
    duplicate paragraph character fraction  0.20

    top 2-gram character fraction           0.20
    top 3-gram character fraction           0.18
    top 4-gram character fraction           0.16

    duplicate 5-gram character fraction     0.15
    duplicate 6-gram character fraction     0.14
    duplicate 7-gram character fraction     0.13
    duplicate 8-gram character fraction     0.12
    duplicate 9-gram character fraction     0.11
    duplicate 10-gram character fraction    0.10
"""


def get_n_grams(words: list[str], n: int) -> list[str]:
    return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]


def find_duplicates(x: list[str]) -> tuple[int, int]:
    unique_x = set()
    duplicate_chars = 0
    duplicate_elements = 0
    for element in x:
        if element in unique_x:
            duplicate_chars += len(element)
            duplicate_elements += 1

        else:
            unique_x.add(element)
    return duplicate_elements, duplicate_chars


def find_top_duplicate(x: list[str]) -> int:
    counter = Counter()
    for element in x:
        counter[element] += 1
    if not counter:
        return 0
    top_n_gram = counter.most_common(1)[0]
    return len(top_n_gram[0]) * top_n_gram[1]


def find_all_duplicate(words: list[str], n: int) -> int:
    n_words = len(words)
    unique = set()
    repeated_chars, idx = 0, 0
    while idx < n_words - n + 1:
        n_gram = "".join(words[idx : idx + n])
        if n_gram in unique:
            repeated_chars += len(n_gram)
            idx += n
        else:
            unique.add(n_gram)
            idx += 1
    assert repeated_chars <= len("".join(words))
    return repeated_chars


class GopherRepetitionFilter(BaseFilter):
    name = "👯 Gopher Repetition"
    _requires_dependencies = ["nltk", "langcodes"]

    def __init__(
        self,
        dup_line_frac: float | None = 0.35,
        dup_para_frac: float | None = 0.35,
        dup_line_char_frac: float | None = 0.2,
        dup_para_char_frac: float | None = 0.2,
        top_n_grams: tuple[tuple[int, float], ...] = ((2, 0.25), (3, 0.23), (4, 0.21)),
        dup_n_grams: tuple[tuple[int, float], ...] = (
            (5, 0.20),
            (6, 0.19),
            (7, 0.18),
            (8, 0.17),
            (9, 0.16),
            (10, 0.15),
        ),
        exclusion_writer: DiskWriter = None,
        do_filter: bool = True,
    ):
        """

        Args:
            dup_line_frac:
            dup_para_frac:
            dup_line_char_frac:
            dup_para_char_frac:
            top_n_grams:
            dup_n_grams:
            exclusion_writer:
            do_filter: If true does perform filtering (a new dataset will be created with only the datapoints that passed the filtering)
        """
        super().__init__(exclusion_writer)

        self.dup_line_frac = dup_line_frac
        self.dup_para_frac = dup_para_frac
        self.dup_line_char_frac = dup_line_char_frac
        self.dup_para_char_frac = dup_para_char_frac
        self.top_n_grams = top_n_grams
        self.dup_n_grams = dup_n_grams
        self.paragraph_exp = re.compile(r"\n{2,}")
        self._line_splitter = re.compile("\n+")
        self.do_filter = do_filter

    def filter(self, doc) -> bool | tuple[bool, str]:
        from langcodes import Language
        from nltk.tokenize import word_tokenize

        text = doc.text
        detected_language = (
            Language.get(doc.metadata["language"]).language_name().lower()
        )

        paragraphs = self.paragraph_exp.split(text.strip())
        lines = self._line_splitter.split(text)

        try:
            words = word_tokenize(text, language=detected_language)
        except:
            logger.info("Tokenizer falling back to Dutch")
            words = word_tokenize(text, language="dutch")

        # Define computation logic for each stat
        stats = {
            "dup_para_frac": lambda: (
                find_duplicates(paragraphs)[0] / len(paragraphs)
                if len(paragraphs) > 0
                else 0
            ),
            "dup_para_char_frac": lambda: (
                find_duplicates(paragraphs)[1] / len(text) if len(text) > 0 else 0
            ),
            "dup_line_frac": lambda: (
                find_duplicates(lines)[0] / len(lines) if len(lines) > 0 else 0
            ),
            "dup_line_char_frac": lambda: (
                find_duplicates(lines)[1] / len(text) if len(text) > 0 else 0
            ),
            "top_n_grams": lambda: [
                (n, find_top_duplicate(get_n_grams(words, n)) / len(text))
                for n, _ in self.top_n_grams
            ],
            "dup_n_grams": lambda: [
                (n, find_all_duplicate(words, n) / len(text))
                for n, _ in self.dup_n_grams
            ],
        }

        # Compute or retrieve each stat from metadata
        for stat_name, compute_stat in stats.items():
            if stat_name not in doc.metadata:
                doc.metadata[stat_name] = compute_stat()

        if not self.do_filter:
            return True

        # Filtering based on computed stats
        if self.dup_para_frac and doc.metadata["dup_para_frac"] > self.dup_para_frac:
            return False, "dup_para_frac"

        if (
            self.dup_para_char_frac
            and doc.metadata["dup_para_char_frac"] > self.dup_para_char_frac
        ):
            return False, "dup_para_char_frac"

        if self.dup_line_frac and doc.metadata["dup_line_frac"] > self.dup_line_frac:
            return False, "dup_line_frac"

        if (
            self.dup_line_char_frac
            and doc.metadata["dup_line_char_frac"] > self.dup_line_char_frac
        ):
            return False, "dup_line_char_frac"

        for n, n_frac in self.top_n_grams:
            top_n_gram_frac = next(
                (frac for n_gram, frac in doc.metadata["top_n_grams"] if n_gram == n), 0
            )
            if top_n_gram_frac > n_frac:
                return False, f"top_{n}_gram"

        for n, n_frac in self.dup_n_grams:
            dup_n_gram_frac = next(
                (frac for n_gram, frac in doc.metadata["dup_n_grams"] if n_gram == n), 0
            )
            if dup_n_gram_frac > n_frac:
                return False, f"duplicated_{n}_n_grams"

        return True
