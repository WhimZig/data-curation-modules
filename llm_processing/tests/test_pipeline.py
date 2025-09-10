from datatrove.data import Document, DocumentsPipeline
from datatrove.executor.base import PipelineExecutor
from datatrove.executor.local import LocalPipelineExecutor
from gptnl_llm_processing.pipeline_step import LLMProcessingStep, RowSplitterOrCombiner
from tests import examples
from tests.utils import requires_gpu

# model_name = "/projects/prjs0986/.hf_cache_dir/hub/models--microsoft--phi-4/snapshots/187ef0342fff0eb3333be9f00389385e95ef0b61/"
model_name = "microsoft/phi-4"

prompt = """Given the following sentences, produce a fluent and coherent paragraph that contains all the information in the sentences. Do not generate any information that is not in the sentences. Ensure that the paragraph is grammatically and syntactically correct in Dutch. Do not produce any additional text, only the paragraph.
Sentences:
{text}

Paragraph:
"""


def output_printer(
    data: DocumentsPipeline, rank: int = 0, world_size: int = 1
) -> DocumentsPipeline:
    for document in data:
        print("OUTPUT_PRINTER", document.text)
        yield document


def test_run_light():
    pipeline = [
        [
            Document(text=examples.EXAMPLE_1, id="1"),
            Document(text=examples.EXAMPLE_2, id="2"),
        ],
        RowSplitterOrCombiner(split=True),
        output_printer,
        # ParquetWriter(
        #     output_folder="outputs_splitted",
        # ),
        RowSplitterOrCombiner(split=False),
        # LLMProcessingStep(model_name=model_name, prompt=prompt),
        output_printer,
        # ParquetWriter(
        #     output_folder="outputs",
        # ),
    ]
    executor: PipelineExecutor = LocalPipelineExecutor(
        pipeline=pipeline, workers=1, tasks=1
    )
    print(executor.run())


@requires_gpu()
def test_run():
    pipeline = [
        [
            Document(text=examples.EXAMPLE_1, id="1"),
            Document(text=examples.EXAMPLE_2, id="2"),
        ],
        RowSplitterOrCombiner(split=True),
        output_printer,
        # ParquetWriter(
        #     output_folder="outputs_splitted",
        # ),
        RowSplitterOrCombiner(split=False),
        LLMProcessingStep(model_name=model_name, prompt=prompt),
        output_printer,
        # ParquetWriter(
        #     output_folder="outputs",
        # ),
    ]
    executor: PipelineExecutor = LocalPipelineExecutor(
        pipeline=pipeline, workers=1, tasks=1
    )
    print(executor.run())


if __name__ == "__main__":
    test_run()
