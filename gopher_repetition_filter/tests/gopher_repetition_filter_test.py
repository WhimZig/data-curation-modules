from unittest.mock import patch

import pytest
from datatrove.data import Document
from gptnl_gopher_repetition_filter import GopherRepetitionFilter
from langcodes import Language
from nltk.tokenize import word_tokenize

TEXT_LF_1 = (
    "I wish it need not have happened in my time,' said Frodo. 'So do I,' said Gandalf, 'and so do all who live to "
    "see such times. But that is not for them to decide. All we have to decide is what to do with the time that is "
    "given us.'"
)


def check_filter(filter, doc, filter_reason):
    filter_result = filter.filter(doc)
    assert type(filter_result) == tuple
    assert filter_result[1] == filter_reason


def get_doc(text, url=None, language="en"):
    return Document(text, id="0", metadata={"url": url, "language": language})


def test():
    # Empty test so that pytest doesn't complain about no tests being present.
    gopher_repetition = GopherRepetitionFilter(
        dup_line_frac=0.3,
        dup_para_frac=0.3,
        dup_line_char_frac=0.2,
        dup_para_char_frac=0.2,
        top_n_grams=((2, 0.2), (3, 0.18), (4, 0.16)),
        dup_n_grams=(
            (5, 0.15),
            (6, 0.14),
            (7, 0.13),
            (8, 0.12),
            (9, 0.11),
            (10, 0.10),
        ),
    )
    check_filter(gopher_repetition, get_doc("I am your father.\n" * 4), "dup_line_frac")
    check_filter(
        gopher_repetition, get_doc("I am your father.\n\n" * 4), "dup_para_frac"
    )
    text = (
        "I am groot.\n\n"
        + "You are a wizard.\n\n"
        + "I am your father.\n\n"
        + f"{'x' * 30}.\n\n" * 2
    )
    check_filter(gopher_repetition, get_doc(text), "dup_para_char_frac")
    doc = get_doc(
        "I am groot.\n"
        + "You are a wizard.\n"
        + "I am your father.\n"
        + f"{'x' * 40}.\n" * 2
    )
    check_filter(gopher_repetition, doc, "dup_line_char_frac")
    check_filter(
        gopher_repetition, get_doc("I am Frank, I am Frank, I am Frank"), "top_2_gram"
    )
    doc = get_doc("I am Frank, you are Jhon. I am Frank. I am Frank you are Jhon")
    check_filter(gopher_repetition, doc, "top_3_gram")
    doc = get_doc("I am Frank, you are Jhon. I am Frank. I am Frank you are Jhon")
    check_filter(gopher_repetition, doc, "top_3_gram")
    doc = get_doc("I am a solo traveller " * 4 + TEXT_LF_1)
    check_filter(gopher_repetition, doc, "duplicated_5_n_grams")


@pytest.mark.parametrize(
    "text,fast_text_lang_code,nltk_lang_code",
    [
        ("Das Wetter ist heute wunderschon.", "de", "german"),
        ("The cat sat on the windowsill, watching the birds outside", "en", "english"),
        ("Jeg elsker at gå ture i parken om morgenen.", "da", "danish"),
        ("Jag tycker om att laga mat på helgerna.", "sv", "swedish"),
        ("Ek hou daarvan om langs die strand te stap.", "af", "afrikaans"),
        ("Ik hâld fan it lêzen fan boeken.", "fy", "western frisian"),
        ("Ik hou van fietsen langs de grachten.", "nl", "dutch"),
    ],
)
def test_lang_code_comp(text: str, fast_text_lang_code: str, nltk_lang_code: str):
    """Checks if the lang code is working between fastext and nltk."""

    detected_language = Language.get(fast_text_lang_code).language_name().lower()

    assert detected_language == nltk_lang_code

    # Handle specific cases for Afrikaans and Western Frisian
    if fast_text_lang_code in ["af", "fy"]:
        with pytest.raises(LookupError):
            assert detected_language == nltk_lang_code
            assert word_tokenize(text, language=detected_language)
    else:
        assert detected_language == nltk_lang_code
        assert word_tokenize(text, language=detected_language)


@pytest.mark.parametrize(
    "text,fast_text_lang_code",
    [
        ("Ek hou daarvan om langs die strand te stap.", "af"),
        ("Ik hâld fan it lêzen fan boeken.", "fy"),
    ],
)
@patch("loguru.logger.info")
def test_trigger_execept_statement(mock_print, text, fast_text_lang_code):
    """Test if it is falling back to dutch language if lang not covered by nltk."""
    doc = get_doc(text=text, language=fast_text_lang_code)
    gopher_repetition = GopherRepetitionFilter()  # Replace with your actual class name

    gopher_repetition.filter(doc)
    mock_print.assert_called_once_with("Tokenizer falling back to Dutch")
