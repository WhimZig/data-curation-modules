from typing import Any

from datatrove.pipeline.formatters.base import BaseFormatter


class PunctuationFormatter(BaseFormatter):
    name = "🔳🔲 Punctuation Formatter"

    def __init__(
        self,
        punctuation_unicode: dict[str, str] | None = None,
        *args: Any,
        **kwargs: Any
    ):
        """Normalize unicode punctuations to English punctuations in text samples.

        Ref:
        https://github.com/modelscope/data-juicer/blob/main/data_juicer/ops/mapper/punctuation_normalization_mapper.py
        """
        super().__init__(*args, **kwargs)

        if punctuation_unicode is None:
            self.punctuation_unicode = {
                "，": ",",
                "。": ".",
                "、": ",",
                "„": '"',
                "”": '"',
                "“": '"',
                "«": '"',
                "»": '"',
                "１": '"',
                "」": '"',
                "「": '"',
                "《": '"',
                "》": '"',
                "´": "'",
                "∶": ":",
                "：": ":",
                "？": "?",
                "！": "!",
                "（": "(",
                "）": ")",
                "；": ";",
                "–": "-",
                "—": " - ",
                "．": ". ",
                "～": "~",
                "’": "'",
                "…": "...",
                "━": "-",
                "〈": "<",
                "〉": ">",
                "【": "[",
                "】": "]",
                "％": "%",
                "►": "-",
            }

    def format(self, text: str) -> str:

        new_text = "".join([self.punctuation_unicode.get(c, c) for c in text])

        return new_text
