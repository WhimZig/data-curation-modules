import re

from datatrove.data import Document
from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.pipeline.writers.disk_base import DiskWriter

CITATION_REGEX = re.compile(r"\[\d*]|\[edit]|\[citation needed]")
END_PUNCTUATION = (".", "?", "!", '"', "'")
ELLIPSIS = "..."
POLICY_SUBSTRINGS = [
    "terms of use",
    "privacy policy",
    "cookie policy",
    "uses cookies",
    "use of cookies",
    "use cookies",
]


class C4QualityFilter(BaseFilter):
    r"""Applies heuristic rules from [C4](https://jmlr.org/papers/volume21/20-074/20-074.pdf).

    - We only retained lines that ended in a terminal punctuation mark (! . " ?)
    - We discarded any page with fewer than 5 sentences and only retained lines that
        contained at least 3 words
    - [NOT IMPLEMENTED] We removed any page that contained any word on the “List of
        Dirty, Naughty, Obscene or Otherwise Bad Words”
    - We removed any line with the word Javascript.
    - We removed any page where the phrase “lorem ipsum” appeared
    - We removed any pages that contained a curly bracket
    Additional filters not mentioned on the list from the paper but on the code:
    - Remove lines with one word over 1000 chars
    - Remove lines with cookies and terms of use keywords

    Reference implementation: https://github.com/tensorflow/datasets/blob/master/tensorflow_datasets/text/c4_utils.py#L197
    Args:
        exclusion_writer: optionally pass in a writer that will save the dropped
            documents
        split_paragraph: by default (as in the paper) split on "\n".
            Set to "False" to apply the filters to each sentence instead of to each line
        remove_citations: remove wikipedia style citations from the text
        filter_no_terminal_punct: remove lines without terminal punctuation marks
        min_num_sentences: remove documents that do not have at least this number of
            sentences (after line filtering). set to -1 to disable
        min_words_per_line: drop lines without this min number of words
        max_word_length: drop lines where at least one word has more than this number of
            characters
        filter_lorem_ipsum: drop documents that contain "lorem ipsum"
        filter_javascript: drop lines mentioning "javascript"
        filter_curly_bracket: drop documents containing {
        filter_policy: drop lines containing any of the phrases in POLICY_SUBSTRINGS
    """

    name = "⛰ C4 Quality"
    _requires_dependencies = ["nltk", "langcodes", "language_data"]

    def __init__(
        self,
        exclusion_writer: DiskWriter = None,
        split_paragraph: bool = True,  # default as used on c4. Set to "False" to split with sent_tokenize
        remove_citations: bool = True,
        filter_no_terminal_punct: bool = True,
        min_num_sentences: int = 5,  # set to -1 to disable
        min_words_per_line: int = 3,  # set to -1 to disable
        max_word_length: int = 1000,  # set to -1 to disable
        filter_lorem_ipsum: bool = True,
        filter_javascript: bool = True,
        filter_curly_bracket: bool = True,
        filter_policy: bool = True,
        do_filter: bool = True,
    ):
        super().__init__(exclusion_writer)
        self.split_paragraph = split_paragraph
        self.remove_citations = remove_citations
        self.filter_no_terminal_punct = filter_no_terminal_punct
        self.min_num_sentences = min_num_sentences
        self.min_words_per_line = min_words_per_line
        self.max_word_length = max_word_length
        self.filter_lorem_ipsum = filter_lorem_ipsum
        self.filter_javascript = filter_javascript
        self.filter_curly_bracket = filter_curly_bracket
        self.filter_policy = filter_policy
        self.do_filter = do_filter

    def filter(self, doc: Document) -> bool | tuple[bool, str]:
        from langcodes import Language
        from nltk.tokenize import sent_tokenize

        # Detect language
        detected_language = (
            Language.get(doc.metadata["language"]).language_name().lower()
        )

        # Initialize the variables only if they are not already in the metadata
        if "num_sentences" not in doc.metadata:
            lines = (
                doc.text.splitlines()
                if self.split_paragraph
                else sent_tokenize(doc.text, language=detected_language)
            )

            num_sentences = 0
            kept_lines = []

            # Conditions and actions mapped to their corresponding logic
            conditions = {
                "line-filter-too_long_word": lambda line: (
                    self.max_word_length != -1
                    and any(len(word) > self.max_word_length for word in line.split())
                ),
                "line-filter-no_terminal_punc": lambda line: (
                    self.filter_no_terminal_punct
                    and (not line.endswith(END_PUNCTUATION) or line.endswith(ELLIPSIS))
                ),
                "line-filter-too_few_words": lambda line: (
                    len(line.split()) < self.min_words_per_line
                ),
                "line-filter-javascript": lambda line: (
                    self.filter_javascript and "javascript" in line.lower()
                ),
                "line-filter-policy": lambda line: (
                    self.filter_policy
                    and any(p in line.lower() for p in POLICY_SUBSTRINGS)
                ),
            }

            # Process each line
            for line in lines:
                line = line.strip()
                self.stat_update("line-total")

                # Apply each condition and skip the line if any condition is met
                for stat_name, condition in conditions.items():
                    if condition(line):
                        self.stat_update(stat_name)
                        break
                else:
                    # Handle conditions that lead to immediate document rejection
                    line_l = line.lower()
                    if self.filter_lorem_ipsum and "lorem ipsum" in line_l:
                        return False, "lorem_ipsum"
                    if self.filter_curly_bracket and "{" in line:
                        return False, "curly_bracket"

                    # Remove citations if necessary
                    if self.remove_citations:
                        line = CITATION_REGEX.sub("", line)

                    # Count sentences and keep the line
                    num_sentences += (
                        len(sent_tokenize(line, language=detected_language))
                        if self.split_paragraph
                        else 1
                    )
                    kept_lines.append(line)
                    self.stat_update("line-kept")

            doc.metadata["num_sentences"] = num_sentences

        else:
            # If stats are already in metadata, retrieve them
            pass

        # Final check on the number of sentences
        if not self.do_filter:
            return True

        if doc.metadata["num_sentences"] < self.min_num_sentences:
            return False, "too_few_sentences"

        # Reconstruct the document text from kept lines in metadata
        doc.text = ("\n" if self.split_paragraph else " ").join(kept_lines).strip()
        return True
