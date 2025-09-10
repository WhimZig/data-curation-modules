from unittest.mock import patch

import pytest
from datatrove.data import Document
from gptnl_gopher_quality_filter import GopherQualityFilter
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
    gopher_quality = GopherQualityFilter(
        min_doc_words=10, max_doc_words=1000, min_avg_word_length=2
    )
    check_filter(gopher_quality, get_doc("I am too small..."), "gopher_short_doc")
    check_filter(gopher_quality, get_doc("I am " * 20), "gopher_below_avg_threshold")
    check_filter(
        gopher_quality, get_doc("interconnection " * 20), "gopher_above_avg_threshold"
    )
    check_filter(gopher_quality, get_doc("# comment " * 20), "gopher_too_many_hashes")
    check_filter(
        gopher_quality, get_doc("... comment " * 20), "gopher_too_many_ellipsis"
    )
    text = "the ./!*?<><> apple <?////> orange  ++ interconnection !<>??? have" * 20
    check_filter(gopher_quality, get_doc(text), "gopher_below_alpha_threshold")
    assert gopher_quality(get_doc(TEXT_LF_1))

    # Check if it also works in other languages
    check_filter(
        gopher_quality, get_doc("Ik ben te klein...", language="nl"), "gopher_short_doc"
    )
    check_filter(
        gopher_quality,
        get_doc("ik a " * 20, language="nl"),
        "gopher_below_avg_threshold",
    )
    check_filter(
        gopher_quality,
        get_doc("j' ai " * 20, language="fr"),
        "gopher_below_avg_threshold",
    )

    assert gopher_quality(
        get_doc(text="Das Wetter ist heute wunderschon.", language="de")
    )
    assert gopher_quality(
        get_doc(text="Das Wetter ist heute wunderschon.", language="de")
    )
    assert gopher_quality(
        get_doc(text="Jeg elsker at gå ture i parken om morgenen.", language="da")
    )
    assert gopher_quality(
        get_doc(text="Jag tycker om att laga mat på helgerna.", language="sv")
    )
    assert gopher_quality(
        get_doc(text="Ek hou daarvan om langs die strand te stap.", language="af")
    )
    assert gopher_quality(
        get_doc(text="Ik hâld fan it lêzen fan boeken.", language="fy")
    )


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
    gopher_quality = GopherQualityFilter()  # Replace with your actual class name

    gopher_quality.filter(doc)
    mock_print.assert_called_once_with("Tokenizer falling back to Dutch")
