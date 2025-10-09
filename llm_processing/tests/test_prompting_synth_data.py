from gptnl_llm_processing.model import LLMProcessing
from tests.examples import *
from tests.utils import requires_gpu

model_name = "microsoft/phi-4"
# if offline
# model_name = "/projects/prjs0986/.hf_cache_dir/hub/models--microsoft--phi-4/snapshots/187ef0342fff0eb3333be9f00389385e95ef0b61/"

prompt = """Given the following sentences, produce a fluent and coherent paragraph that contains all the information in the sentences. Do not generate any information that is not in the sentences. Ensure that the paragraph is grammatically and syntactically correct in Dutch. Do not produce any additional text, only the paragraph.
Sentences:
{text}

Paragraph:
"""

inputs = [
    EXAMPLE_1,
    EXAMPLE_2,
    EXAMPLE_3,
    EXAMPLE_4,
    EXAMPLE_5,
    EXAMPLE_6,
    EXAMPLE_7,
    EXAMPLE_8,
    EXAMPLE_9,
]


@requires_gpu()
def test_processing():
    model = LLMProcessing(model_name=model_name, prompt=prompt)

    outputs_without_chat = model.process_texts(
        texts=inputs, max_tokens=200, temperature=0.1, use_chat=False
    )
    outputs_with_chat = model.process_texts(
        texts=inputs, max_tokens=200, temperature=0.1, use_chat=True
    )
    print("\n\n")
    print("without chat")
    print(outputs_without_chat)
    print("\nwith chat")
    print(outputs_with_chat)
    assert len(outputs_without_chat) == len(inputs)
    assert len(outputs_with_chat) == len(inputs)
    for o in outputs_without_chat + outputs_with_chat:
        assert o
        assert len(o) > 10
        assert len(o) < 1000
        if o in outputs_with_chat:
            # check that no markdown headings are here (hallucinations)
            assert "#" not in o, o


if __name__ == "__main__":
    test_processing()
