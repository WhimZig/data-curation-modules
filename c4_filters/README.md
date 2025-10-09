# C4 filter

## C4QualityFilter

Applies heuristic rules from [C4](https://jmlr.org/papers/volume21/20-074/20-074.pdf).

Reference implementation [here](https://github.com/tensorflow/datasets/blob/master/tensorflow_datasets/text/c4_utils.py#L197).

## C4ParagraphFilter

Applies paragraph filtering from [mC4](https://github.com/tensorflow/datasets/blob/master/tensorflow_datasets/text/c4_utils.py#L551).

## C4BadWordsFilter

Bad words filter from C4.

## Dev notes

Numpy has been version pinned to `>=1.25.0,<2.0.0` because Datatrove needs this version.
