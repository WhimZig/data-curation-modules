# Regular Expression Formatter

This module enables the application of regular expressions in the data curation pipeline.

## Dev notes

The init() function is to be instantiated with:
- A list of regex patterns.
- A list of replacement strings for the corresponding pattern.
- A list of regex flags, each corresponding to a pattern.
- args and **kwargs

This allows for multiple specific regular expressions to be formatted at the same time.
