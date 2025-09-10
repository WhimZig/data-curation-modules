import pytest
from datatrove.data import Document
from gptnl_quality_analysis import PerplexityStats
from pytest import main


def get_doc_w_meta(text, url=None, language="en"):
    return Document(text, id="0", metadata={"url": url, "language": language})


def get_doc_w_o_meta(text):
    return Document(text, id="0")


class TestPerplexityStats:

    def test_init_model(self):
        """Test if the config yaml and the jsonargparser compile correctly."""
        perp_stats = PerplexityStats(output_folder="mock/datatset.parquet")
        # assert perp_stats.models["english"]
        assert perp_stats.models["dutch"]

    @pytest.mark.parametrize(
        "doc,expected_results",
        [
            (get_doc_w_o_meta("Ik eet graag koekjes!"), "perplexity_dutch"),
            (
                get_doc_w_o_meta("This is a complex pieve of text!"),
                "perplexity_english",
            ),
            (
                get_doc_w_meta("Ik eet graag koekjes!", language="nl"),
                "perplexity_dutch",
            ),
            (
                get_doc_w_meta("This is a complex pieve of text!", language="en"),
                "perplexity_english",
            ),
            (get_doc_w_o_meta("Ceci est un text francais"), "perplexity_dutch"),
        ],
    )
    def test_extract_stats(self, doc: Document, expected_results: str) -> None:
        perp_stats = PerplexityStats(output_folder="mock/datatset.parquet")
        result = perp_stats.extract_stats(doc)
        assert isinstance(result, dict)
        assert list(result.keys())[0].startswith(expected_results)
        assert isinstance(list(result.values())[0], float)
        assert list(result.values())[0] > 0


if __name__ == "__main__":
    main()
