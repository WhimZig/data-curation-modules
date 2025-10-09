import pandas as pd
import pytest
from gptnl_toxic_language_detection import ToxicLanguageDetection

from .conftest import evaluate_formatting

# Load the data and prepare tuples for parameterization
df = pd.read_csv("data/English/toxic_language_test_sentences.csv", sep=";")
testdata = [
    tuple(row)
    for row in df[["Sentence", "Label", "Type", "Toxic_Sentence"]].itertuples(
        index=False
    )
]


@pytest.fixture(scope="class")
def formatter():
    formatter_instance = ToxicLanguageDetection(threshold=0.0)
    yield formatter_instance
    del formatter_instance


@pytest.mark.parametrize(
    "sentence, expected_label, test_type, toxic_sentence", testdata
)
class TestDutchToxicLanguage:
    def test_english_toxic_language(
        self, formatter, sentence, expected_label, test_type, toxic_sentence, request
    ):
        formatted_sentence, metadata = formatter.format(
            sentence, language="en", with_metadata=True
        )

        predicted_label, evaluation_result = evaluate_formatting(
            expected_label, sentence, formatted_sentence, toxic_sentence
        )

        # Use helper function for assertion
        request.node.user_properties.append(("name", "ToxicLanguage"))
        request.node.user_properties.append(("language", "EN"))
        request.node.user_properties.append(("test_type", test_type))
        request.node.user_properties.append(("expected", expected_label))
        request.node.user_properties.append(("predicted", predicted_label))
        request.node.user_properties.append(("sentence", sentence))
        request.node.user_properties.append(("formatted_sentence", formatted_sentence))
        request.node.user_properties.append(("toxic_sentence", toxic_sentence))
        request.node.user_properties.append(("metadata", metadata))
        request.node.user_properties.append(("reason", evaluation_result))

        assert evaluation_result == "pass", evaluation_result
