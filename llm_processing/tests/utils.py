import pytest
from vllm.platforms import current_platform


def requires_gpu():
    return pytest.mark.skipif(
        # not torch.cuda.is_available(), # fails with vllm
        not current_platform.is_cuda(),
        reason="GPU is not available",
    )
