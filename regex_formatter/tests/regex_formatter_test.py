import pytest
import regex as re
from gptnl_regex_formatter import RegexFormatter

testdata = [
    (
        "In Youtube-Commons, many placeholders can occur, such as: [Musik], [Muziek], [Music], [Laughter], [Gelach] etc.",
        [r"\[[a-zA-Z]{0,15}\]"],
        [""],
        [re.DOTALL],
        "In Youtube-Commons, many placeholders can occur, such as: , , , ,  etc.",
    ),
    (
        "How is repetition repetition repetition repetition handled?",
        [r"\b(\w+)\s+\1\s+\1(\s+\1)*\b"],
        [r"\1 \1"],
        [re.S],
        "How is repetition repetition handled?",
    ),
    (
        "How is repetition repetition repetition repetition handled? [Music] [Gelach]",
        [r"\b(\w+)\s+\1\s+\1(\s+\1)*\b", r"\[[a-zA-Z]{0,15}\]"],
        [r"\1 \1", ""],
        [re.DOTALL, re.S],
        "How is repetition repetition handled?  ",
    ),
]


@pytest.mark.parametrize("text, pattern, repl, flags, formatted_text", testdata)
def test(
    text: str,
    pattern: list[str],
    repl: list[str],
    flags: list[int],
    formatted_text: str,
):
    """Checks if the output of the RegexFormatter works correctly."""
    try:
        regex_formatter = RegexFormatter(pattern, repl, flags)
        output = regex_formatter.format(text)
        assert output == formatted_text, (
            f"\nExpected: {formatted_text}"
            f"\nGot     : {output}"
            f"\nInput   : {text}"
            f"\nPattern : {pattern}"
            f"\nRepl    : {repl}"
            f"\nFlags   : {flags}"
        )
    except Exception as e:
        pytest.fail(f"Unexpected error during formatting: {e}")


if __name__ == "__main__":
    for elem in testdata:
        test(
            text=elem[0],
            pattern=elem[1],
            repl=elem[2],
            flags=elem[3],
            formatted_text=elem[4],
        )
