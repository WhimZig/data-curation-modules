import gc
import platform

import pytest
import torch
from vllm.platforms import current_platform


def requires_gpu():
    return pytest.mark.skipif(
        # not torch.cuda.is_available(), # fails with vllm
        not current_platform.is_cuda(),
        reason="GPU is not available",
    )


def requires_snellius():
    return pytest.mark.skipif(
        not platform.node().endswith("snellius.surf.nl"),
        reason="You are not running on snellius",
    )


def cleanup_memory(model):
    if model.vllm_model:
        del model.vllm_model
    if model.model:
        model.model.cpu()
        del model.model
    del model

    gc.collect()
    torch.cuda.empty_cache()
    # very drastic, makes successive usages to CPU (unwanted)
    # device = cuda.get_current_device()
    # device.reset()
