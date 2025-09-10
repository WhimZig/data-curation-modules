import pytest
from gptnl_machine_translation.model import TranslatorModel
from tests import examples
from tests.models import get_model_name_and_use_vllm, model_names
from tests.utils import cleanup_memory, requires_gpu

test_cases = get_model_name_and_use_vllm()


@requires_gpu()
# @pytest.mark.parametrize(
#     "model_name, use_vllm",
#     model_names,
#     use_vllms,
#     indirect=["use_vllms"],
#     scope="module",
# )
@pytest.mark.parametrize("model_name,use_vllm", test_cases, scope="module")
def test_model(model_name: str, use_vllm: bool):
    translator = TranslatorModel(
        model_name=model_name, source_language="Spanish", use_vllm=use_vllm
    )
    assert translator is not None
    assert translator.model_name == model_name
    if use_vllm:
        assert translator.vllm_model is not None
    else:
        assert translator.model is not None
        assert translator.tokenizer is not None
        assert translator.device is not None
    # test translation
    short_text = "Hola, ¿cómo estás?"
    translated_text = translator.translate_texts([short_text])[0]
    assert translated_text is not None
    assert translated_text != short_text
    assert len(translated_text) > 0
    assert any(
        expected in translated_text.lower()
        for expected in ["hoe gaat", "hoe is", "wat is"]
    )
    print(translated_text)
    # test multiple texts: padding (long text batched together with short text)
    translated = translator.translate_texts([short_text, examples.LONG_TEXT])
    print(translated)
    assert any(
        expected in translated[0].lower()
        for expected in ["hoe gaat", "hoe is", "wat is"]
    )

    cleanup_memory(translator)


@pytest.mark.parametrize("model_name", model_names)
def test_tokenize(model_name: str):
    translator = TranslatorModel(
        model_name=model_name,
        disable_model_load=True,
        source_language="Spanish",
        use_vllm=False,
    )
    text = "Hola, ¿cómo estás?"
    tokens = translator.tokenize(text)
    assert tokens is not None
    assert len(tokens) > 0
    assert tokens.shape[0] == 1
    assert tokens.shape[1] > 5
    assert tokens.shape[1] < 20


@pytest.mark.parametrize("model_name", model_names)
def test_tokenize_multiple(model_name: str):
    translator = TranslatorModel(
        model_name=model_name,
        disable_model_load=True,
        source_language="Spanish",
        use_vllm=False,
    )
    texts = ["Hola, ¿cómo estás?", "¡Hola!"]
    tokens = translator.tokenize(texts)
    assert tokens is not None
    assert len(tokens) > 0
    assert tokens.shape[0] == 2
    assert tokens.shape[1] > 5
    assert tokens.shape[1] < 20
    print(tokens)
