import re

from datatrove.data import Document
from datatrove.io import cached_asset_path_or_download
from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.pipeline.writers.disk_base import DiskWriter
from numpy.random import default_rng

_EN_BADWORDS_URL = "https://raw.githubusercontent.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/25e679f03d96baa721cde20db9944649e8d0a844/en"
_BADWORDS_URL = "https://raw.githubusercontent.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/5faf2ba42d7b1c0977169ec3611df25a3c08eb13/"
_BADWORDS_LANGS = [
    "ar",
    "cs",
    "da",
    "de",
    "en",
    "eo",
    "es",
    "fa",
    "fi",
    "fil",
    "fr",
    "fr-CA-u-sd-caqc",
    "hi",
    "hu",
    "it",
    "ja",
    "kab",
    "ko",
    "nl",
    "no",
    "pl",
    "pt",
    "ru",
    "sv",
    "th",
    "tlh",
    "tr",
    "zh",
]
# Words that are allowed since they are common subwords in languages without
# spaces. These each filter >10% of documents of their language when disallowed.
_BADWORDS_ALLOWLIST = {"ja": {"sm", "グロ", "女の子"}, "zh": {"性"}}


class C4BadWordsFilter(BaseFilter):
    """Badwords filter from C4.

    Args:
        keep_fraction (float): what percentage of pages containing bad words should be
            kept
        fail_on_missing_language (bool) whether to fail when a document has an unknown
            language
        seed (int): used for the uniform distribution generator for use with
            keep_fraction
        default_language (str): what language for samples without language in their
            metadata
    """

    name = "⛰ C4 Badwords"

    def __init__(
        self,
        keep_fraction: float = 0.0,
        fail_on_missing_language: bool = True,
        seed: int = None,
        default_language: str = "en",
        exclusion_writer: DiskWriter = None,
    ):
        super().__init__(exclusion_writer)
        self.keep_fraction = keep_fraction
        self.fail_on_missing_language = fail_on_missing_language
        self._badwords_regex: dict[str, re.Pattern] = {}
        self.uniform = default_rng(seed).uniform
        self.default_language = default_language

    def _get_badwords(self, lang: str):
        if lang not in self._badwords_regex:
            if lang not in _BADWORDS_LANGS:
                if self.fail_on_missing_language:
                    raise ValueError(
                        f'There is not badwords list available for "{lang}". '
                        f"Set fail_on_missing_language=False to continue anyway."
                    )
                else:
                    return None
            local_path = cached_asset_path_or_download(
                _BADWORDS_URL + lang if lang != "en" else _EN_BADWORDS_URL,
                namespace="filters",
                subfolder="c4_badwords",
            )
            badwords: set[str] = set()
            # load from file
            with open(local_path) as f:
                badwords.update(line.strip() for line in f)
            for lang, allowlist in _BADWORDS_ALLOWLIST.items():
                badwords -= allowlist

            words = [re.escape(w) for w in badwords]
            self._badwords_regex[lang] = (
                # For Japanese, Thai, and Chinese, do not require word separations.
                re.compile("|".join(words))
                if lang in ("ja", "th", "zh")
                # For other languages, match only when flanked by non-word chars.
                else re.compile(r"(?:\W|^)({})(?:\W|$)".format("|".join(words)))
            )
        return self._badwords_regex[lang]

    def filter(self, doc: Document) -> bool | tuple[bool, str]:
        lang = str(doc.metadata.get("language", self.default_language))
        badwords_regex = self._get_badwords(lang)
        if badwords_regex is None:
            self.stat_update("missing_badwords_lang", f"missing_badwords_lang_{lang}")
            return True
        badwords_found = badwords_regex.search(doc.text.lower())
        if badwords_found is not None:
            self.stat_update(
                "documents_with_badwords", f"documents_with_badwords_{lang}"
            )
            if self.keep_fraction > 0.0 and self.uniform() < self.keep_fraction:
                self.stat_update(
                    "document_kept_with_badwords", f"document_kept_with_badwords_{lang}"
                )
                return True
            self.stat_update(f"document_removed_with_badwords_{lang}")
            return False, "document_removed_with_badwords"
        return True
