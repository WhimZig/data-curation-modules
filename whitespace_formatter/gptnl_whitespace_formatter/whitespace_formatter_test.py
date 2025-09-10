from . import WhitespaceFormatter


def test():
    f = WhitespaceFormatter()

    assert (
        f.format(
            "f"
            " "
            "   "
            " "
            " "
            " "
            " "
            " "
            " "
            " "
            " "
            " "
            " "
            " "
            " "
            " "
            " "
            "　"
            "\u200b"
            "‌"
            "‍"
            "⁠"
            "￼"
            ""
            "f"
        )
        == "f                         f"
    )
