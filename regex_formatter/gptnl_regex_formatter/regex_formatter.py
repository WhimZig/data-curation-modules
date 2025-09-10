from typing import Any, Optional

import regex as re
from datatrove.pipeline.formatters.base import BaseFormatter


class RegexFormatter(BaseFormatter):
    name = "🔳🔲 Punctuation Formatter"

    def __init__(
        self,
        pattern: list[str],
        repl: list[str] = [""],
        flags: Optional[list[int]] = [re.DOTALL],
        *args: Any,
        **kwargs: Any
    ):
        """Replaces a certain sequence of string using a regex expression."""
        super().__init__(*args, **kwargs)

        self.pattern = [
            (
                p[2:-1]
                if (len(p) > 2)
                and (
                    (p.startswith("r'") and p.endswith("'"))
                    or (p.startswith('r"') and p.endswith('"'))
                )
                else p
            )
            for p in pattern
        ]

        self.repl = repl
        self.flags = flags

    def format(self, text: str) -> str:
        """Format the text based on certain regex expressions."""

        # Iterate over patterns, replacements, and flags simultaneously
        for pat, repl, flag in zip(self.pattern, self.repl, self.flags):
            # Apply the substitution directly
            text = re.sub(pat, repl, text, flags=flag)

        return text
