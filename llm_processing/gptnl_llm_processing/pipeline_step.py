import uuid
from itertools import islice

from datatrove.data import Document, DocumentsPipeline
from datatrove.pipeline.base import PipelineStep
from datatrove.utils.typeshelper import StatHints
from gptnl_llm_processing.model import LLMProcessing


# from itertools import batched # minimum python3.12
def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


class LLMProcessingStep(PipelineStep):
    type = "🤖 - LLM"
    name = "Use LLM to process text"

    def __init__(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int | None = None,  # if None, taken from len(input_text) / 3
        temperature: float = 0.1,
        batch_size: int = 10,
        use_chat_template: bool = True,
        debug_mode: bool = False,
    ):
        self.model_name = model_name
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.batch_size = batch_size
        self.use_chat_template = use_chat_template
        self.debug_mode = debug_mode
        if self.debug_mode:
            print("prompt template:", self.prompt)
        super().__init__()

    def run(
        self, data: DocumentsPipeline, rank: int = 0, world_size: int = 1
    ) -> DocumentsPipeline:
        model = LLMProcessing(
            model_name=self.model_name,
            prompt=self.prompt,
        )

        for batch in batched(data, n=self.batch_size):
            with self.track_time(unit="batch"):
                docs = list(batch)
                input_texts = [doc.text for doc in docs]
                max_tokens = self.max_tokens or max(len(t) for t in input_texts) // 3
                output_texts = model.process_texts(
                    input_texts,
                    max_tokens=max_tokens,
                    temperature=self.temperature,
                    use_tqdm=False,
                    print_prompt=self.debug_mode,
                    use_chat_template=self.use_chat_template,
                )
                for doc, output_text in zip(docs, output_texts):
                    self.stat_update(StatHints.total)
                    input_text = doc.text
                    if not output_text:
                        # empty string
                        if self.debug_mode:
                            raise ValueError(output_text)
                        self.stat_update(StatHints.dropped)
                    else:
                        self.stat_update(StatHints.forwarded)
                        # replace text with transformed one
                        doc.text = output_text
                        assert doc.text, "No text"
                        if "meta" not in doc.metadata:
                            doc.metadata["meta"] = {}
                        doc.metadata["meta"].update(
                            {
                                "llm_processing_model_name": self.model_name,
                                "llm_processing_prompt_template": self.prompt,
                                "llm_processing_input_text": input_text,
                                "llm_processing_max_tokens": max_tokens,
                                "llm_processing_temperature": self.temperature,
                            }
                        )
                        yield doc


class RowSplitterOrCombiner(PipelineStep):
    type = "👥 - Splits and combines rows"
    name = "Splits rows based on delimiter or recombines them back together"

    def __init__(
        self,
        split: bool,
        separator: str = "\n",
        identifier_metadata_field: str = "row_splitter_id",
    ):
        """If split==True splits the rows at the separator.
        If split==False, recocombines them with the separator.
        The identifier_metadata_field is generated during split and deleted during combination.
        """
        self.split = split
        self.separator = separator
        self.identifier_metadata_field = identifier_metadata_field
        super().__init__()

    def get_original_id(self, doc: Document) -> str:
        value = doc.metadata.get(self.identifier_metadata_field)
        assert value, f"identifier_metadata_field is {value}, {self.split}"
        return str(value)

    def join_texts(self, texts: list[str]) -> str:
        return self.separator.join(texts)

    def split_text(self, text: str) -> list[str]:
        return text.split(sep=self.separator)

    def run(
        self, data: DocumentsPipeline, rank: int = 0, world_size: int = 1
    ) -> DocumentsPipeline:
        if self.split == True:
            return self.split_data(data=data)
        else:
            return self.combine_data(data=data)

    def split_data(self, data: DocumentsPipeline):
        for i, doc in enumerate(data):
            self.stat_update(StatHints.total)
            with self.track_time():
                split_id = str(uuid.uuid4())
                text = doc.text
                splitted_text = self.split_text(text=text)
                for t in splitted_text:
                    doc.text = t
                    doc.metadata[self.identifier_metadata_field] = split_id
                    self.stat_update(StatHints.forwarded)
                    yield doc

    def combine_data(self, data: DocumentsPipeline):
        current_id = None
        current_doc = None
        texts_with_current_id = []
        for i, doc in enumerate(data):
            self.stat_update(StatHints.total)
            with self.track_time():
                original_id = self.get_original_id(doc)
                if current_id:
                    if original_id == current_id:
                        # continuing
                        texts_with_current_id.append(doc.text)
                    else:
                        # started a new original doc
                        # 1. return final previous doc
                        assert current_doc
                        current_doc.text = self.join_texts(texts_with_current_id)
                        del current_doc.metadata[self.identifier_metadata_field]
                        self.stat_update(StatHints.forwarded)
                        yield current_doc
                        # 2. new one
                        current_id = original_id
                        texts_with_current_id = [doc.text]
                        current_doc = doc
                else:
                    # first row, no current set
                    current_id = original_id
                    texts_with_current_id = [doc.text]
                    current_doc = doc
        # yield last doc
        if current_id:
            assert current_doc
            current_doc.text = self.join_texts(texts_with_current_id)
            del current_doc.metadata[self.identifier_metadata_field]
            self.stat_update(StatHints.forwarded)
            yield current_doc
