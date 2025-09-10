import pytest
from datatrove.data import Document, DocumentsPipeline
from datatrove.executor.base import PipelineExecutor
from datatrove.executor.local import LocalPipelineExecutor
from datatrove.pipeline.readers.parquet import ParquetReader
from datatrove.pipeline.writers.parquet import ParquetWriter
from datatrove.utils.stats import MetricStats, PipelineStats
from gptnl_machine_translation.pipeline import SplittedRowsCombiner, TranslatorStep
from tests import examples
from tests.utils import requires_gpu, requires_snellius


def output_printer(
    data: DocumentsPipeline, rank: int = 0, world_size: int = 1
) -> DocumentsPipeline:
    for document in data:
        print("OUTPUT_PRINTER", document.text)
        yield document


@requires_gpu()
def test_run():
    pipeline = [
        [
            Document(text=examples.LONG_TEXT, id="1"),
            Document(text=examples.LONG_TEXT_2, id="2"),
            Document(text=examples.LONG_TEXT_3, id="3"),
            Document(
                text=examples.LONG_TEXT + examples.LONG_TEXT_2 + examples.LONG_TEXT_3,
                id="4",
            ),
        ],
        output_printer,
        TranslatorStep(use_vllm=False),
        output_printer,
    ]
    executor: PipelineExecutor = LocalPipelineExecutor(
        pipeline=pipeline, workers=1, tasks=1
    )
    print(executor.run())


def test_run_chunker():
    pipeline = [
        [
            # Document(text=examples.LONG_TEXT, id="1"),
            Document(text=examples.LONG_TEXT_2, id="2"),
            # Document(text=examples.LONG_TEXT_3, id="3"),
            # Document(
            #     text=examples.LONG_TEXT + examples.LONG_TEXT_2 + examples.LONG_TEXT_3,
            #     id="4",
            # ),
        ],
        # output_printer,
        TranslatorStep(chunk_size=50, use_vllm=False, dry_run=True),
        output_printer,
    ]
    executor: PipelineExecutor = LocalPipelineExecutor(
        pipeline=pipeline, workers=1, tasks=1
    )
    print(executor.run())


def test_run_with_recombine():
    pipeline = [
        [
            Document(text=examples.LONG_TEXT, id="1"),
            Document(text=examples.LONG_TEXT_2, id="2"),
        ],
        # output_printer,
        TranslatorStep(chunk_size=50, use_vllm=False, dry_run=True),
        # output_printer,
        SplittedRowsCombiner(),
    ]
    executor: PipelineExecutor = LocalPipelineExecutor(
        pipeline=pipeline, workers=1, tasks=1
    )
    res = executor.run()
    assert isinstance(res, PipelineStats)
    stats_combiner = res.stats[-1].stats
    forwarded: MetricStats = stats_combiner["forwarded"]
    assert forwarded.n == 2, f"Did not forward correctly 2: {forwarded.n}"
    print(res)


@requires_snellius()
@pytest.mark.skip(reason="TODO")
def test_run_on_splitted_parquet():
    pipeline = [
        ParquetReader(
            data_folder=str(
                "/projects/prjs0986/wp12/curated/spanish-pd-newspapers/pipeline00000_translation_spanish_pd_newspapers_c4538f1/stage1_data_splitting_balanced/"
            ),
            file_progress=True,
            doc_progress=True,
            glob_pattern="*1893_00000.parquet",
        ),
        # output_printer,
        TranslatorStep(
            model_name="ModelSpace/GemmaX2-28-9B-v0.1",
            stop_at=1,  # 1,
            batch_stop_at=None,
            chunk_size=256,  # 1024,
            batch_size=128,  # TODO: go bigger, see if there is limit!!
            # dry_run=True,
        ),
        ParquetWriter(
            output_folder="out_gemma2_256_vllm",
            # output_folder="out_madlad_256_c",
        ),
    ]
    executor: PipelineExecutor = LocalPipelineExecutor(
        pipeline=pipeline, workers=1, tasks=1
    )
    print(executor.run())


if __name__ == "__main__":
    # test_run()
    test_run_on_splitted_parquet()
    # test_run_chunker()
    # test_run_with_recombine()
