from typing import Any

from datatrove.pipeline.formatters.base import BaseFormatter


class WhitespaceFormatter(BaseFormatter):
    name = "🗻 Whitespace Formatter"

    def __init__(
        self, VARIOUS_WHITESPACES: dict[str] | None = None, *args: Any, **kwargs: Any
    ):
        """Normalize whitesapces in text samples.

        Ref:
        https://github.com/modelscope/data-juicer/blob/main/data_juicer/ops/mapper/whitespace_normalization_mapper.py


        :param args: extra args
        :param kwargs: extra args
        """
        super().__init__(*args, **kwargs)

        if VARIOUS_WHITESPACES is None:
            self.VARIOUS_WHITESPACES = {
                " ",
                " ",
                " ",
                " ",
                " ",
                " ",
                " ",
                " ",
                " ",
                " ",
                " ",
                " ",
                " ",
                " ",
                " ",
                "　",
                "\u200b",
                "‌",
                "‍",
                "⁠",
                "￼",
                "",
            }

    def format(self, text: str) -> str:

        text = text.strip()
        # replace all kinds of whitespaces with ' '
        new_text = "".join(
            [char if char not in self.VARIOUS_WHITESPACES else " " for char in text]
        )
        return new_text
