from typing import Any

import ftfy
from datatrove.pipeline.formatters.base import BaseFormatter


class FTFYFormatter(BaseFormatter):
    name = "😎 FTFY"
    _requires_dependencies = ["ftfy"]

    def __init__(self, normalization: str | None = None, *args: Any, **kwargs: Any):
        """Initialization method.

        :param normalization: the specified form of Unicode normalization mode, which
            can be one of ['NFC', 'NFKC', 'NFD', and 'NFKD'], default 'NFC'.
        :param args: extra args
        :param kwargs: extra args
        """
        super().__init__(*args, **kwargs)
        if normalization and len(normalization) > 0:
            self.normalization = normalization.upper()
        else:
            self.normalization = "NFC"

        if self.normalization.upper() not in ["NFC", "NFKC", "NFD", "NFKD"]:
            raise ValueError(
                f"Normalization mode [{normalization}] is not "
                "supported. Can only be one of "
                '["NFC", "NFKC", "NFD", "NFKD"]'
            )

    def format(self, text: str) -> str:
        return ftfy.fix_text(text, normalization=self.normalization)
