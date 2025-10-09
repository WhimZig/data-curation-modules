from gptnl_machine_translation.batch import create_batches
from gptnl_machine_translation.long_document_translator import LongDocumentTranslator
from tests.examples import LONG_TEXT, LONG_TEXT_2, LONG_TEXT_3


def test_create_batches():
    long_text = LONG_TEXT + LONG_TEXT_2 + LONG_TEXT_3  # 636 tokens
    batch_size = 2
    chunk_size = 100
    translator = LongDocumentTranslator(
        dry_run=True,
        source_language="Spanish",
        use_vllm=False,
        chunk_mode="tokens",
    )
    tokenized_text = translator.tokenize(long_text)[0]

    total_tokens = tokenized_text.shape[0]
    batches, offsets_ids = create_batches(
        tokenized_text, chunk_size=chunk_size, batch_size=batch_size
    )
    sum_tokens = 0
    for batch in batches:
        sum_batch = 0
        for row in batch:
            print(row)
            sum_batch += row.shape[0]
            assert (
                row.shape[0] <= chunk_size
            ), f"shape[0] ({row.shape[0]}) should be less than chunk_size ({chunk_size})"
        assert (
            len(batch) <= batch_size
        ), f"len(batch) ({len(batch)}) should be less than batch_size ({batch_size})"
        sum_tokens += sum_batch
    assert (
        sum_tokens >= total_tokens
    ), f"sum_tokens ({sum_tokens}) should be greater than total_tokens ({total_tokens})"


if __name__ == "__main__":
    test_create_batches()
