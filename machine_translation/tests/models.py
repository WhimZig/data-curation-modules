# which models to test loading
non_llm_models = [
    "google/madlad400-10b-mt",
]
llm_models = [
    "ModelSpace/GemmaX2-28-9B-v0.1",
]
model_names = non_llm_models + llm_models


# @pytest.fixture(scope="module")
def use_vllm_for_model(model_name):
    if model_name in llm_models:
        # llm_models can be run also with vllm
        return [True, False]
    else:
        # other models cannot be run with vllm
        return [False]


def chunk_mode_for_model(model_name):
    if model_name in llm_models:
        # llm_models can only be run with chunk_mode=characters
        return ["characters"]
    else:
        # other models can be chunked in characters or tokens
        return ["characters", "tokens"]


def get_model_name_and_use_vllm():
    result = []
    for model_name in model_names:
        vllms_params = use_vllm_for_model(model_name)
        for vllm in vllms_params:
            result.append((model_name, vllm))
    return result


def get_model_name_and_use_vllm_and_chunk_mode():
    result = []
    for model_name in model_names:
        vllms_params = use_vllm_for_model(model_name)
        chunk_modes = chunk_mode_for_model(model_name)
        for vllm in vllms_params:
            for chunk_mode in chunk_modes:
                result.append((model_name, vllm, chunk_mode))
    return result
