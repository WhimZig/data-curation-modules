from unittest.mock import patch

import pytest
from datatrove.data import Document
from gptnl_nordicpile_quality_filter import NordicPileQualityFilter
from langcodes import Language
from nltk.corpus import stopwords
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
    nordicpile_quality = NordicPileQualityFilter(
        max_digit_fraction=0.2,
        min_mean_med_char=9,
        min_mean_med_word=2.1,
        min_n_char=15,
    )
    check_filter(
        nordicpile_quality, get_doc("I have 12349432"), "nordicpile_digit_fraction"
    ),
    check_filter(
        nordicpile_quality,
        get_doc("I have only"),
        "nordicpile_short_doc",
    )
    check_filter(
        nordicpile_quality,
        get_doc("This text\n " * 3),
        "nordicpile_mean_med_char",
    )
    check_filter(
        nordicpile_quality,
        get_doc(
            "Unbelievable\ntransformations,\nextraordinary\ndevelopments,\nand\nmagnificent\nachievements\ncharacterize\nthe\nphenomenon"
        ),
        "nordicpile_mean_med_word",
    )

    assert nordicpile_quality(get_doc(TEXT_LF_1))


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
            assert stopwords.words(detected_language)
    else:
        assert detected_language == nltk_lang_code
        assert word_tokenize(text, language=detected_language)
        assert stopwords.words(detected_language)


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
    nordicpile_quality = (
        NordicPileQualityFilter()
    )  # Replace with your actual class name

    nordicpile_quality.filter(doc)
    mock_print.assert_called_once_with("Tokenizer falling back to Dutch")
