import uuid
from typing import Literal

from datatrove.data import Document, DocumentsPipeline
from datatrove.pipeline.base import PipelineStep
from datatrove.utils.typeshelper import StatHints
from gptnl_machine_translation.long_document_translator import LongDocumentTranslator


class TranslatorStep(PipelineStep):
    type = "🗣️ - TRANSLATE"
    name = "🇳🇱 - translate to Dutch"

    def __init__(
        self,
        model_name: str = "ModelSpace/GemmaX2-28-9B-v0.1",
        use_vllm: bool = True,
        chunk_mode: Literal["characters", "tokens"] = "characters",
        chunk_size: int = 1024,
        batch_size: int = 128,
        stop_at: int | None = None,
        batch_stop_at: int | None = None,
        dry_run: bool = False,
        source_language: str | None = None,
        destination_language: str = "Dutch",
    ):
        self.model_name = model_name
        self.use_vllm = use_vllm
        self.chunk_mode = chunk_mode
        self.chunk_size = chunk_size
        self.batch_size = batch_size
        self.stop_at = stop_at
        self.batch_stop_at = batch_stop_at
        self.dry_run = dry_run
        self.source_language = source_language
        self.destination_language = destination_language
        super().__init__()

    def run(
        self, data: DocumentsPipeline, rank: int = 0, world_size: int = 1
    ) -> DocumentsPipeline:
        translator = LongDocumentTranslator(
            model_name=self.model_name,
            use_vllm=self.use_vllm,
            chunk_mode=self.chunk_mode,
            chunk_size=self.chunk_size,
            batch_size=self.batch_size,
            batch_stop_at=self.batch_stop_at,
            dry_run=self.dry_run,
            source_language=self.source_language,
            destination_language=self.destination_language,
        )

        for i, doc in enumerate(data):
            if self.stop_at and i >= self.stop_at:
                print(f"early stopping with stop_at={self.stop_at}")
                break
            self.stat_update(StatHints.total)
            with self.track_time():
                row_splitter_id = str(uuid.uuid4())
                for (
                    translated_text_chunk,
                    chunk_id,
                    source_text,
                ) in translator.translate_long_text(
                    long_text=doc.text,
                ):
                    if not translated_text_chunk:
                        # empty string
                        self.stat_update(StatHints.dropped)
                    else:
                        self.stat_update(StatHints.forwarded)
                        doc.text = translated_text_chunk
                        assert doc.text, "No text"
                        if "meta" not in doc.metadata:
                            doc.metadata["meta"] = {}
                        doc.metadata["row_splitter_id"] = row_splitter_id
                        doc.metadata["meta"].update(
                            {
                                "machine_translation_chunk_id": chunk_id,
                                "machine_translation_model_name": self.model_name,
                                "machine_translation_use_vllm": self.use_vllm,
                                "machine_translation_chunk_mode": self.chunk_mode,
                                "machine_translation_chunk_size": self.chunk_size,
                                "machine_translation_batch_size": self.batch_size,
                                # "machine_translation_source_language": self.source_language,
                                "machine_translation_destination_language": self.destination_language,
                                "machine_translation_input_text": source_text,
                            }
                        )
                        yield doc


class SplittedRowsCombiner(PipelineStep):
    type = "👥 - Combine"
    name = "Combine together rows splitted by translation chunking"

    def __init__(self):
        super().__init__()

    def get_original_id(self, doc: Document) -> str:
        # get id and remove it
        id = doc.metadata.pop("row_splitter_id")
        return str(id)

    def remove_row_splitter_id(self, doc: Document):
        # for some reasons the metadata.pop in get_original_id does not run always (maybe a bug in the self.run loop???)
        if "row_splitter_id" in doc.metadata.keys():
            del doc.metadata["row_splitter_id"]

    def join_texts(self, texts: list[str]) -> str:
        return " ".join(texts)

    def join_chunk_ids(self, chunk_ids: list[str]) -> str:
        return ",".join(chunk_ids)

    def run(
        self, data: DocumentsPipeline, rank: int = 0, world_size: int = 1
    ) -> DocumentsPipeline:
        current_id = None
        current_doc = None
        texts_with_current_id = []
        chunks_ids_with_current_id = []
        input_texts_with_current_id = []
        for i, doc in enumerate(data):
            self.stat_update(StatHints.total)
            with self.track_time():
                machine_translation_original_id = self.get_original_id(doc)
                if current_doc:
                    if machine_translation_original_id == current_id:
                        # continuing
                        texts_with_current_id.append(doc.text)
                        chunks_ids_with_current_id.append(
                            doc.metadata["meta"]["machine_translation_chunk_id"]
                        )
                        input_texts_with_current_id.append(
                            doc.metadata["meta"]["machine_translation_input_text"]
                        )
                    else:
                        # started a new original doc
                        # 1. return final previous doc
                        self.update_doc_merge(
                            current_doc,
                            texts=texts_with_current_id,
                            chunk_ids=chunks_ids_with_current_id,
                            input_texts=input_texts_with_current_id,
                        )
                        self.remove_row_splitter_id(current_doc)
                        self.stat_update(StatHints.forwarded)
                        yield current_doc
                        # 2. new one
                        current_id = machine_translation_original_id
                        current_doc = doc
                        texts_with_current_id = [doc.text]
                        chunks_ids_with_current_id = [
                            doc.metadata["meta"]["machine_translation_chunk_id"]
                        ]
                        input_texts_with_current_id = [
                            doc.metadata["meta"]["machine_translation_input_text"]
                        ]
                else:
                    # first row, no current set
                    current_id = machine_translation_original_id
                    current_doc = doc
                    texts_with_current_id = [doc.text]
                    chunks_ids_with_current_id = [
                        doc.metadata["meta"]["machine_translation_chunk_id"]
                    ]
                    input_texts_with_current_id = [
                        doc.metadata["meta"]["machine_translation_input_text"]
                    ]
        # yield last doc
        if current_doc:
            self.update_doc_merge(
                current_doc,
                texts=texts_with_current_id,
                chunk_ids=chunks_ids_with_current_id,
                input_texts=input_texts_with_current_id,
            )
            self.remove_row_splitter_id(current_doc)
            self.stat_update(StatHints.forwarded)
            yield current_doc

    def update_doc_merge(
        self,
        doc: Document,
        texts: list[str],
        chunk_ids: list[str],
        input_texts: list[str],
    ):
        assert doc
        doc.text = self.join_texts(texts)
        doc.metadata["meta"]["machine_translation_chunk_id"] = self.join_chunk_ids(
            chunk_ids
        )
        doc.metadata["meta"]["machine_translation_input_text"] = input_texts
        return doc
