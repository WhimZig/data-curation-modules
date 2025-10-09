# PII Detection

## Description

This module detects and formats Personally Identifiable Information (PII) in text. It identifies various types of PII, such as numerical identifiers like bank accounts, phone numbers, and passports, as well as names and organisations. The detected PII is then replaced with specific masks to anonymize the data, such as replacing an IBAN with `<iban>` or a person's name, like Jan Jansen, with `<person>`. This functionality is particularly useful for preparing data for training language models while preserving privacy.

The structure of this module is as follows:

- `./data/`: The data folder that contains test data, including synthetically generated data in `gptnl_synthetic_pii_data`.
- `./src/`: The source code folder of the module.
- `./tests/`: Test code folder which tests the PII using the data from `gptnl_synthetic_pii_data`.
- `./tests_output/`: Here a CSV file is created after running all of the tests in the `tests` folder.

- `./tests_output/1_analyse_all_test_results.ipynb`: A notebook used to output the `Precision;Recall;F1;TP;FP;TN;FN;` per PII.
- `create_pytest_files.ipynb`: a Jupyter notebook that generates pytest files for testing the PII detection module.
- `pii_quick_test_notebook.ipynb`: A Jupyter notebook that contains examples on how to use the module.

## Usage

You can look in the Jupyter notebook `./pii_quick_test_notebook.ipynb` to checkout the examples on how to use the module.

### Basic example

Simple example would be:

```python
from gptnl_pii_mappers import PII_EmailAddress, PII_Person_Flair_Large

pii_email_formatter = PII_EmailAddress()
print(pii_email_formatter.format("Hello! Welkom bij PII Detection 101, we ontvangen al uw antwoorden graag op pii_detection@tno.nl. Alvast bedankt & tot ziens!"))

pii_person_formatter = PII_Person_Flair_Large()
print(pii_person_formatter.format("Hello! Mijn naam is Jan Henk en dit is een test. We werken aan NER PII Detection.", language="nl"))
```

Outputs:

```
Hello! Welkom bij PII Detection 101, <e-mail_address>. Alvast bedankt & tot ziens!

Hello! Mijn naam is <PER> en dit is een test. We werken aan NER PII Detection.
```

### Validation

You can create validation functions like such and create new formatters with appropriate factory and add the validator function as argument:
(In this example XLM_RoBERTa is used as example NER Formatter, any from the package can be used.)

```python
from gptnl_pii_mappers import NER_XLM_RoBERTa, PII_XLM_RoBERTa_Dutch_Formatter, ner_factory

def is_Peter(match: str) -> bool:
    """
    Checks if a given string starts with 'Peter'.

    Args:
        match (str): The string to check.

    Returns:
        bool: True if the string starts with 'Peter', False otherwise.
    """
    return match.startswith('Peter')
PII_Validated_Person = ner_factory(class_=PII_XLM_RoBERTa_Dutch_Formatter, validator=is_Peter, **NER_XLM_RoBERTa["person"])
```

### NER Grouping

Grouping can be enabled in NER Formatters like such:

```python
PII_Grouped_Person = ner_factory(class_=PII_XLM_RoBERTa_Dutch_Formatter, **NER_XLM_RoBERTa["person"], group=True)
pii_grouped_person_formatter = PII_Grouped_Person()
print(pii_grouped_person_formatter.format("Hello! Mijn naam is Jan Henk en dit is een test. We werken aan NER PII Detection. Bert heeft grote koeien.", language="nl"))
```

Outputs:

```
Hello! Mijn naam is <PER1> en dit is een test. We werken aan NER PII Detection. <PER2> heeft grote koeien.
```

### Chains

Furthermore, you can create `ChainFormatter`'s that contain will sequentially run multiple different PII Formatters:

```python
from gptnl_pii_mappers import pii_chain_formatter_class_factory, PII_CreditCardNumber, PII_IBAN, PII_EuropeanVATNumber, PII_CreditCardCVVCode, PII_CreditCardExpiryDate

PII_Banking = pii_chain_formatter_class_factory(
    ordered_list_of_formatter_classes=[
        PII_CreditCardNumber,
        PII_IBAN,
        PII_EuropeanVATNumber,
        PII_CreditCardCVVCode,
        PII_CreditCardExpiryDate,
    ]
)

banking_formatter = PII_Banking()
print(banking_formatter.format("""Hierbij zijn enkele voorbeelden van persoonlijke gegevens:
Het IBAN-nummer van de gemeentelijke rekening voor Rotterdam is NL12BNGH0285133675.
U kunt het ook geschreven vinden als NL12 BNGH 0285 1336 75 met spaties ertussen.
Mijn creditcardgegevens zijn als volgt: nummer 3576 8292 3893 9730, beveiligingscode (cvv) 202, en deze verloopt op 12/29.
Let op: deze gegevens zijn alleen voor testgebruik en niet authentiek. Alvast bedankt voor de medewerking.
"""))
```

Outputs:

```
Hierbij zijn enkele voorbeelden van persoonlijke gegevens:
Het IBAN-nummer van de gemeentelijke rekening voor Rotterdam is <iban>.
U kunt het ook geschreven vinden als <iban> met spaties ertussen.
Mijn creditcardgegevens zijn als volgt: nummer <credit_card_number>, beveiligingscode (cvv) <credit_card_cvv_code>, en deze verloopt op <credit_card_expiry_date>.
Let op: deze gegevens zijn alleen voor testgebruik en niet authentiek. Alvast bedankt voor de medewerking.
```

### Language dependend

There are also cases, especially in larger multiligual datasets, were you are only interested for PII related to a specific language. For this we have designed the LanguageFormatter, which you can define to run specific formatters given a detected language.

Example:

```python
PII_NER = language_factory(
    language_to_formatter_classes={
        "nl": chain_factory(
            ordered_list_of_formatter_classes=[
                PII_DutchLicensePlateNumber,
                PII_DutchPhoneNumber,
                PII_DutchIdentityNumberBSN,
                PII_DutchIdentityDocumentNumber,
                ner_factory(class_=PII_XLM_RoBERTa_Dutch_Formatter, **NER_XLM_RoBERTa["person_and_organisation"], group=True),
            ]
        ),
        "en": chain_factory(
            ordered_list_of_formatter_classes=[
                PII_UKDriversLicense,
                PII_UKNationalInsuranceNumber,
                PII_UKUniqueTaxpayerReferenceNumber,
                PII_UK_USPassportNumber,
                ner_factory(class_=PII_Flair_Large_Formatter, **NER_FLAIR["person_and_organisation"], group=True),

            ]
        ),
    }
)
```

### Custom Detector with GLiNER

- Base model: [GLiNER](https://github.com/urchade/GLiNER)
- Finetuned for PII: [E3-JSI GLiNER PII](https://huggingface.co/E3-JSI/gliner-multi-pii-domains-v1)

Furthermore, it is possible to create your own general PII detector using GLiNER. All credits go to the people that have developed and trained this model.

```python
from gptnl_pii_mappers import ner_factory, PII_GLiNERFormatter

PII_Banking_GLiNER = ner_factory(class_=PII_GLiNERFormatter, entity_types=["credit card number", "iban", "european vat number", "credit card cvv code", "cvc code", "cvv code", "credit card expiry date", "expiry date"])
gliner_banking_formatter = PII_Banking_GLiNER()
print(gliner_banking_formatter.format("""Hierbij zijn enkele voorbeelden van persoonlijke gegevens:
Het IBAN-nummer van de gemeentelijke rekening voor Rotterdam is NL12BNGH0285133675.
U kunt het ook geschreven vinden als NL12 BNGH 0285 1336 75 met spaties ertussen.
Mijn creditcardgegevens zijn als volgt: nummer 3576 8292 3893 9730, beveiligingscode (cvv) 202, en deze verloopt op 12/29.
Let op: deze gegevens zijn alleen voor testgebruik en niet authentiek. Alvast bedankt voor de medewerking.
""", language="nl"))
```

Outputs:

```
Hierbij zijn enkele voorbeelden van persoonlijke gegevens:
Het IBAN-nummer van de gemeentelijke rekening voor Rotterdam is <iban>.
U kunt het ook geschreven vinden als <iban> met spaties ertussen.
Mijn creditcardgegevens zijn als volgt: nummer <credit_card_number>, beveiligingscode (cvv) <credit_card_cvv_code>, en deze verloopt op <credit_card_expiry_date>.
Let op: deze gegevens zijn alleen voor testgebruik en niet authentiek. Alvast bedankt voor de medewerking.
```

For NER PII Formatters it is important that you include the language, otherwise it will default to the dutch language. The NER models support a specific list of languages.

## Installation of package for Development or Usage

### Conda

Create a new conda environment with `conda create -n <env_name> python=3.10`, or select your existing one.
Install the package and its dependencies in your environment with `pip install -e .` with python version `3.10` or higher.

### Poetry

Depencencies are managed via [Poetry](https://python-poetry.org/), so first make sure that you have installed it locally. If you are using `bash`, you can install it with the following command. Other installation methods can be found [here](https://python-poetry.org/docs/#installation).

```bash
curl -sSL https://install.python-poetry.org | python3 -
poetry completions bash >> ~/.bash_completion
poetry config virtualenvs.in-project true # So virtual environments are created in the project directory
```

Create a virtual environment and install the dependencies:

```bash
poetry shell
poetry install
```

In case you are using `vscode`, and the installed dependencies are not regonized, you can run the following command `poetry env info --path` to get the path to the virtual environment.
Next, in `vscode`, open the command palette (CTRL+SHIFT+P or F1) and run `Python: Select Interpreter` and select the virtual environment.

## Testing

To run the tests for the PII detection module, you can use the following command: `pytest tests --tb=no -rN -s --disable-warnings` in the main directory.
