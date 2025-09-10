# NordicPile missing quality filter

Nordic Pile is making use of the Gopher quality filters.
However, in the paper additional filters are added such as the digit fraction, mean line length and the document length
Reference: https://arxiv.org/pdf/2303.17183

## Post install

After running `poetry install`, make sure to run `poetry run post-install`!

This may also be necessary in the code base using this module by running `import nltk; nltk.download("punkt"); nltk.download("punkt_tab")` in your code.

## Dev notes

Numpy has been version pinned to `>=1.25.0,<2.0.0` because Datatrove needs this version.
