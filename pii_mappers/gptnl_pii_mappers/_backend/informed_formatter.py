import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from datatrove.data import Document, DocumentsPipeline
from datatrove.pipeline.base import PipelineStep
from datatrove.pipeline.formatters.pii import PIIReplacer
from datatrove.utils.batching import batched
from datatrove.utils.typeshelper import StatHints
from loguru import logger


class InformedFormatter(PipelineStep, ABC):
    type = "✂️ - INFORMED FORMAT"

    def __init__(self, batch_size: int = 1):
        """Initialize the InformedFormatter.

        Args:
            batch_size (int, optional): Number of documents to process in a batch. Defaults to 1.
        """
        super().__init__()
        self.batch_size = batch_size
        if (
            self.batch_size > 1
            and type(self).format_batch == InformedFormatter.format_batch
        ):
            logger.warning(
                f"{batch_size=} > 1 but {self} does not implement a custom format_batch method."
            )

    @abstractmethod
    def format(
        self, text: str, language: str = "", with_metadata: bool = False
    ) -> tuple[str, list]:
        """Format a single document's text.

        Args:
            text (str): The text to format.
            language (str, optional): The language of the text. Defaults to "".
            with_metadata (bool, optional): Whether to return metadata. Defaults to False.

        Returns:
            Tuple[str, Dict[str, Any]]: The formatted text and associated metadata.
        """
        raise NotImplementedError

    def format_batch(self, batch: list[Document]) -> list[tuple[str, list]]:
        """Format a batch of documents. Override this method for optimized batch processing.

        Args:
            batch (List[Document]): A list of documents to format.

        Returns:
            List[Tuple[str, Dict[str, Any]]]: A list of tuples containing formatted text and metadata for each document.
        """
        return [
            self.format(
                doc.text,
                doc.metadata.get("language", "") if doc.metadata else "",
                with_metadata=True,
            )
            for doc in batch
        ]

    def run(
        self, data: DocumentsPipeline, rank: int = 0, world_size: int = 1
    ) -> DocumentsPipeline:
        """Process the documents pipeline by formatting each document.

        Args:
            data (DocumentsPipeline): The input documents pipeline.
            rank (int, optional): Rank of the current process in distributed settings. Defaults to 0.
            world_size (int, optional): Total number of processes in distributed settings. Defaults to 1.

        Yields:
            Document: The formatted document.
        """
        for batch in batched(data, self.batch_size):
            if self.batch_size > 1:
                self.stat_update("batches")
            with self.track_time("batch" if self.batch_size > 1 else None):
                formatted_results = self.format_batch(batch)

            for doc, (formatted_text, metadata_list) in zip(
                batch, formatted_results, strict=False
            ):
                self.stat_update(StatHints.total)
                if doc.text != formatted_text:
                    self.stat_update("formatted")
                    self.update_doc_stats(doc)
                    doc.text = formatted_text
                    if metadata_list:
                        logger.debug(
                            f"Updating metadata for document ID {doc.id}: {metadata_list}"
                        )
                        self._update_metadata(doc, metadata_list)
                else:
                    self.stat_update("not_formatted")
                    self.update_doc_stats(doc, [])
                yield doc

    def _update_metadata(
        self, doc: Document, metadata_list: list[dict[str, Any]]
    ) -> None:
        """Update the document's metadata with the provided metadata.

        Args:
            doc (Document): The document to update.
            metadata_list (list[dict[str, Any]]): The metadata to add or update.
        """
        if not hasattr(doc, "metadata") or doc.metadata is None:
            doc.metadata = {}

        doc.metadata["PII"] = metadata_list


class PIISmartReplacerAndCounter(PIIReplacer):
    def __init__(
        self,
        regex: str,
        replacements: list[str] | str,
        validator: Callable[[str], bool] | None = None,
        keywords: list[str] | None = None,
        keyword_range: int | None = None,
    ):
        """Initialize the PIIReplacerCounter.

        :param regex: The regex pattern to search for PII.
        :param replacements: The replacement string or a tuple of replacement strings.
        :param key_words: A tuple of keyword strings that must be near a match to trigger replacement.
        :param range_: The number of characters within which a key_word must appear before or after the match.
        :param validator: An optional callable to validate matches before replacement.
        """
        super().__init__(regex, replacements, validator)
        self.keywords = keywords
        self.keyword_range = keyword_range

    def replace_no_kewords(self, text: str) -> tuple[str, int]:
        """Replace all occurrences of the regex pattern in the given text with a sequence of replacements and the number of replacements made."""
        actual_replacement_count = 0  # New counter for actual replacements

        def get_replacement(matchobj):
            nonlocal actual_replacement_count
            if self.validator and not self.validator(matchobj.group(0)):
                return matchobj.group(0)
            replacement = self.replacements[self._replace_i]
            self._replace_i = (self._replace_i + 1) % len(self.replacements)
            actual_replacement_count += 1  # Increment only when a replacement is made
            return replacement

        new_text = self.regex.sub(repl=get_replacement, string=text)
        return new_text, actual_replacement_count

    def replace_keywords(self, text: str) -> tuple[str, int]:
        """Replace occurrences of the regex pattern with replacements only if a key_word is within the specified range.

        :param text: The input text to process.
        :return: A tuple containing the new text and the count of actual replacements made.
        """
        actual_replacement_count = 0  # Counter for actual replacements

        def get_replacement(matchobj: re.Match) -> str:
            nonlocal actual_replacement_count
            match_start, match_end = matchobj.span()

            # Define the search window around the match
            search_start = max(0, match_start - self.keyword_range)
            search_end = min(len(text), match_end + self.keyword_range)
            context = text[search_start:search_end].lower()

            # Check if any key_word is present in the context
            if not any(key_word.lower() in context for key_word in self.keywords):
                return matchobj.group(0)  # Do not replace

            # If a validator is provided, use it to decide on replacement
            if self.validator and not self.validator(matchobj.group(0)):
                return matchobj.group(0)  # Do not replace

            # Perform the replacement
            replacement = self.replacements[self._replace_i]
            self._replace_i = (self._replace_i + 1) % len(self.replacements)
            actual_replacement_count += 1
            return replacement

        # Perform the substitution using the custom replacement function
        new_text = self.regex.sub(repl=get_replacement, string=text)
        return new_text, actual_replacement_count

    def replace(self, text: str) -> tuple[str, int]:
        if self.keywords and self.keyword_range:
            return self.replace_keywords(text)
        else:
            return self.replace_no_kewords(text)


def split_text_into_chunks(
    text: str, max_chunk_length: int, split_type="words"
) -> list[str]:
    if split_type == "sentences":
        from flair.splitter import SegtokSentenceSplitter

        splitter = SegtokSentenceSplitter()
        sentences = splitter.split(text)
        for sentence in sentences:
            if len(sentence.text) > max_chunk_length:
                print(
                    f"Warning: sentence chunk is above max_chunk_length {max_chunk_length}: {sentence.text}"
                )

        return [sentence.text + " " for sentence in sentences]
    elif split_type == "words":
        chunks = []
        current_chunk = []
        current_length = 0
        for word in text.split(" "):
            word_len = len(word)
            if current_chunk:
                word_len += 1  # Account for space
            if current_length + word_len > max_chunk_length:
                chunks.append(" ".join(current_chunk) + " ")
                current_chunk = [word]
                current_length = word_len
            else:
                current_chunk.append(word)
                current_length += word_len
        if current_chunk:
            chunks.append(" ".join(current_chunk) + " ")
        return chunks
    elif split_type == "characters":
        return [
            text[i : i + max_chunk_length]
            for i in range(0, len(text), max_chunk_length)
        ]
    else:
        raise ValueError(
            "Argument 'split_type' should be of ['sentences', 'words', 'characters']"
        )


def calculate_offsets(chunks: list[str]) -> list[int]:
    offset = 0
    offsets = []
    for chunk in chunks:
        offsets.append(offset)
        offset += len(chunk)
    return offsets


def adjust_indices(entities: list[dict], offset: int) -> list[dict]:
    for entity in entities:
        entity["start"] += offset
        entity["end"] += offset
    return entities
