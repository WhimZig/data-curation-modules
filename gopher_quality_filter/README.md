# Gopher quality filter

Filter to apply Gopher's quality heuristic rules.

Reference: https://arxiv.org/pdf/2112.11446.pdf

Applies heuristic rules from [datatrove](https://jmlr.org/papers/volume21/20-074/20-074.pdf).

Reference implementation [here](https://github.com/huggingface/datatrove/blob/main/src/datatrove/pipeline/filters/gopher_quality_filter.py).

## Dev notes

Numpy has been version pinned to `>=1.25.0,<2.0.0` because Datatrove needs this version.
