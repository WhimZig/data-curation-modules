from abc import ABC, abstractmethod
from typing import Any

from datatrove.data import Document, DocumentsPipeline
from datatrove.pipeline.base import PipelineStep
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
                        # logger.debug(
                        #     f"Updating metadata for document ID {doc.id}: {metadata_list}"
                        # )
                        self._update_metadata(doc, metadata_list)
                    else:
                        self._update_metadata(
                            doc,
                            [
                                {
                                    "label": "",
                                    "score": 0.0,
                                    "sentence": "",
                                    "start_index": 0,
                                }
                            ],
                        )
                else:
                    self.stat_update("not_formatted")
                    self.update_doc_stats(doc)
                    self._update_metadata(
                        doc,
                        [{"label": "", "score": 0.0, "sentence": "", "start_index": 0}],
                    )
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

        doc.metadata["ToxicLanguage"] = metadata_list
