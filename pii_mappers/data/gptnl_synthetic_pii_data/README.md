# How to get started:
The Dataset is split in Dutch and English sentences, each in their own "language" folder.
Each folder contains PII specfic `.csv` files that can be loaded in with pandas with `sep=";"`.

The columns of each file are: `Sentence;Label;Type;Entity`, where:

- `Sentence`: a sentence containing personally identifiable information (PII)
- `Label`: a tag indicating the type of PII present in the sentence
- `Type`: The type refers to the test cases, so it is either a `True` type, meaning the PII is present, `False` type, meaning the PII is not present and `Edge`, a type indicating boundary cases where the presence of PII is ambiguous or challenging to detect but the label is 1.
- `Entity`: the specific piece of PII identified in the sentence.

## Example Usage:
In a pytest file you can run:

```python
import pandas as pd
import pytest
from tests.conftest import assert_formatting
from gptnl_pii_mappers import PII_EmailAddress


# Load the data and prepare tuples for parameterization
df = pd.read_csv("data/gptnl_synthetic_pii_data/Dutch/PII_EmailAddress.csv", sep=";")
testdata = [tuple(row) for row in df[["Sentence", "Label", "Type", "Entity"]].itertuples(index=False)]

@pytest.fixture(scope="class")
def formatter():
    formatter_instance = PII_EmailAddress()
    yield formatter_instance
    del formatter_instance

@pytest.mark.parametrize("sentence, expected_label, test_type, entity", testdata)
class TestDutchPII_EmailAddress:
    def test_dutch_emailaddress(self, formatter, sentence, expected_label, test_type, entity, request):
        formatted_sentence = formatter.format(sentence, language="dutch")
        # Use helper function for assertion
        request.node.user_properties.append(("name", "EmailAddress"))
        request.node.user_properties.append(("model_name", ""))
        request.node.user_properties.append(("language", "Dutch"))
        request.node.user_properties.append(("detection_type", "REGEX"))
        request.node.user_properties.append(("test_type", test_type))
        request.node.user_properties.append(("expected", expected_label))
        request.node.user_properties.append(("predicted", int(sentence != formatted_sentence)))
        request.node.user_properties.append(("sentence", sentence))
        request.node.user_properties.append(("formatted_sentence", formatted_sentence))
        request.node.user_properties.append(("entity", entity))
        assert_formatting(expected_label, sentence, formatted_sentence)
```

This will load in the data from the csv file and then run the tests using the pytest framework to ensure that the PII_EmailAddress formatter correctly identifies and formats email addresses in Dutch sentences. Make sure to have the necessary dependencies installed and the correct file paths set up before running the tests. This is further described in the README of the repository.
