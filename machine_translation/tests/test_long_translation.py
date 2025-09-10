import pytest
from gptnl_machine_translation.long_document_translator import LongDocumentTranslator
from tests import examples
from tests.models import get_model_name_and_use_vllm_and_chunk_mode, model_names
from tests.utils import cleanup_memory, requires_gpu

test_cases = get_model_name_and_use_vllm_and_chunk_mode()


@requires_gpu()
@pytest.mark.parametrize("model_name,use_vllm,chunk_mode", test_cases)
def test_translate_long(model_name: str, use_vllm: bool, chunk_mode: str):
    batch_size = 3
    if chunk_mode == "characters":
        chunk_size = 600
    else:
        chunk_size = 150
    translator = LongDocumentTranslator(
        model_name=model_name,
        chunk_size=chunk_size,
        batch_size=batch_size,
        source_language="Spanish",
        use_vllm=use_vllm,
        chunk_mode=chunk_mode,
    )

    long_text = examples.LONG_TEXT

    short_text = "Hola, ¿cómo estás?"

    for translated_text_chunk, chunk_id in translator.translate_long_text(
        long_text=short_text
    ):
        print(translated_text_chunk, chunk_id)
        assert (
            len(translated_text_chunk) < 50
        ), f"There's probably something wrong with the padding. Translated chunk: {translated_text_chunk}"
        assert any(
            expected in translated_text_chunk.lower()
            for expected in ["hoe gaat", "hoe is", "wat is"]
        ), translated_text_chunk

    for translated_text_chunk, chunk_id in translator.translate_long_text(
        long_text=long_text
    ):
        print(translated_text_chunk, chunk_id)
        assert "Lorem Ipsum" in translated_text_chunk

    # TODO
    for translated_text_chunk, chunk_id in translator.translate_long_text(
        long_text=examples.LONG_TEXT_WITH_NEWLINES
    ):
        print(translated_text_chunk, chunk_id)

    cleanup_memory(translator)


if __name__ == "__main__":
    # for model_name in model_names:
    model_name = model_names[1]
    test_translate_long(model_name=model_name, use_vllm=True, chunk_mode="characters")
