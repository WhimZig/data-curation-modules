import requests
from luhn import verify as credit_card_verification
from schwifty import IBAN

from ._backend.chain_factory import pii_chain_formatter_class_factory as chain_factory
from ._backend.language_factory import (
    pii_language_formatter_class_factory as language_factory,
)
from ._backend.ner_factory import (
    HuggingFaceNERFormatter,
    PII_Flair_Large_Formatter,
    PII_GLiNERFormatter,
    PII_RobBERT_V2_Dutch_Formatter,
    PII_XLM_RoBERTa_Dutch_Formatter,
)
from ._backend.ner_factory import pii_ner_formatter_class_factory as ner_factory
from ._backend.ner_pii_list import NER_NAME_TO_MASK  # Used in tests
from ._backend.ner_pii_list import (
    NER_FLAIR,
    NER_GLiNER,
    NER_RobBERT,
    NER_XLM_RoBERTa,
)
from ._backend.private_ai_factory import (
    pii_privateai_formatter_class_factory as privateai_factory,
)
from ._backend.private_ai_pii_list import (
    DatasetName_To_PrivateAI_Mapping,
    PrivateAI_GDPR,
    PrivateAI_TNO,
)
from ._backend.regex_factory import pii_regex_formatter_class_factory as regex_factory
from ._backend.regex_pii_list import REGEX_NAME_TO_MASK  # Used in tests
from ._backend.regex_pii_list import (
    AUSTRALIAN_REGEX,
    BANKING_REGEX,
    BELGIAN_REGEX,
    CANADIAN_REGEX,
    COMMON_REGEX,
    COMPUTER_REGEX,
    DUTCH_REGEX,
    UK_REGEX,
    US_REGEX,
)

NAME_TO_MASK = {}
NAME_TO_MASK.update(NER_NAME_TO_MASK)
NAME_TO_MASK.update(REGEX_NAME_TO_MASK)


def is_not_on_wikidata(match: str) -> bool:
    """Checks if a given string does not match any entities on Wikidata.

    This function sends a request to the Wikidata API to search for entities matching
    the provided string. If no matching entities are found, the function returns True.

    Args:
        match (str): The string to search for on Wikidata.

    Returns:
        bool: True if the string does not match any entities on Wikidata, False otherwise.
    """
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": match,
        "language": "en",
        "limit": 5,
        "format": "json",
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Check if we have results and if there's an entity with an ID
    return "search" in data and len(data["search"]) == 0


def is_valid_credit_card(match: str) -> bool:
    """Validates a credit card number using the Luhn algorithm.

    This function removes spaces and hyphens from the input string,
    then checks if the credit card number passes the Luhn verification test.

    Args:
        match (str): The credit card number to validate.

    Returns:
        bool: True if the credit card number is valid, otherwise False.
    """
    match = match.replace(" ", "").replace("-", "")
    try:
        if credit_card_verification(match):
            return True
    except Exception:
        pass
    return False


def is_valid_bsn(input_string: str) -> bool:
    """Validates a Dutch Burgerservicenummer (BSN) using the 11-proef (modulo 11) algorithm.

    The function first strips the input string of any non-digit characters, then applies
    a standard check whereby each digit of the nine-digit BSN is multiplied by an associated
    decreasing weight, and the results summed. A valid BSN will produce a checksum that is
    divisible by 11, with specific conditions for the final digit.

    Algorithm details can be found at:
    https://nl.wikipedia.org/wiki/Burgerservicenummer#11-proef

    Args:
        input_string (str): The input string containing the potential BSN. May contain non-digit characters.

    Returns:
        bool: True if the input string contains a valid BSN; False otherwise.
    """
    number = "".join([char for char in input_string if char.isdigit()])
    list_digits = [int(digit) for digit in number]

    if len(list_digits) != 9:
        return False

    mod_11_index = list(range(1, 10))[::-1]
    mod_11_index[-1] = -1

    checksum = [
        digit * mod_index
        for digit, mod_index in zip(list_digits, mod_11_index, strict=False)
    ]
    checksum = sum(checksum) % 11

    return checksum == 0


def is_valid_IBAN_account(match: str) -> bool:
    """Determine if the provided string is a valid IBAN.

    This function attempts to validate the given string as an International Bank
    Account Number (IBAN). It uses an IBAN library that raises an exception when
    the IBAN is not valid. The function returns True if the match is a valid IBAN
    and False otherwise.

    Args:
        match (str): The string to be validated as an IBAN.

    Returns:
        bool: True if the string is a valid IBAN, False if it is not.
    """
    try:
        # The module throws an error if the IBAN is not valid
        IBAN(match).validate(validate_bban=True)
        return True
    except Exception:
        pass
    return False


PII_PrivateAI_TNO = privateai_factory(**PrivateAI_TNO)
PII_PrivateAI_GDPR = privateai_factory(**PrivateAI_GDPR)

PII_CreditCardNumber = regex_factory(
    validator=is_valid_credit_card, **BANKING_REGEX["credit_card_number"]
)
PII_IBAN = regex_factory(validator=is_valid_IBAN_account, **BANKING_REGEX["iban"])
PII_DutchIdentityNumberBSN = regex_factory(
    validator=is_valid_bsn, **DUTCH_REGEX["dutch_identity_number_bsn"]
)

PII_EmailAddress = regex_factory(**COMPUTER_REGEX["e-mail_address"])
PII_IPAddress = regex_factory(**COMPUTER_REGEX["ip_address"])
PII_URL = regex_factory(**COMPUTER_REGEX["url"])
PII_MACAddress = regex_factory(**COMPUTER_REGEX["mac_address"])
PII_FilePath = regex_factory(**COMPUTER_REGEX["file_path"])

# PII_CreditCardNumber = regex_factory(**BANKING_REGEX["credit_card_number"])
PII_CreditCardCVVCode = regex_factory(**BANKING_REGEX["credit_card_cvv_code"])
PII_CreditCardExpiryDate = regex_factory(**BANKING_REGEX["credit_card_expiry_date"])
# PII_IBAN = regex_factory(**BANKING_REGEX["iban"])
PII_EuropeanVATNumber = regex_factory(**BANKING_REGEX["european_vat_number"])

PII_InternationalPhoneNumber = regex_factory(
    **COMMON_REGEX["international_phone_number"]
)

PII_DutchLicensePlateNumber = regex_factory(**DUTCH_REGEX["dutch_license_plate_number"])
PII_DutchPhoneNumber = regex_factory(**DUTCH_REGEX["dutch_phone_number"])
# PII_DutchIdentityNumberBSN = regex_factory(**DUTCH_REGEX["dutch_identity_number_bsn"])
PII_DutchIdentityDocumentNumber = regex_factory(
    **DUTCH_REGEX["dutch_identity_document_number"]
)
PII_DutchVreemdelingenDocumentNumber = regex_factory(
    **DUTCH_REGEX["dutch_vreemdelingen_document_number"]
)
PII_DutchBelgianDriversLicenseNumber = regex_factory(
    **DUTCH_REGEX["dutch_belgian_drivers_license_number"]
)

PII_BelgianIdentityNumber = regex_factory(**BELGIAN_REGEX["belgian_identity_number"])
PII_BelgianLicencePlateNumber = regex_factory(
    **BELGIAN_REGEX["belgian_licence_plate_number"]
)
PII_BelgianPhoneNumber = regex_factory(**BELGIAN_REGEX["belgian_phone_number"])
PII_BelgianPassportNumber = regex_factory(**BELGIAN_REGEX["belgian_passport_number"])
PII_DutchBelgianDriversLicenseNumber = regex_factory(
    **BELGIAN_REGEX["dutch_belgian_drivers_license_number"]
)

PII_AustralianDriversLicenseNumber = regex_factory(
    **AUSTRALIAN_REGEX["australian_drivers_license_number"]
)
PII_AustralianBankAccountNumber = regex_factory(
    **AUSTRALIAN_REGEX["australian_bank_account_number"]
)
PII_AustralianPassportNumber = regex_factory(
    **AUSTRALIAN_REGEX["australian_passport_number"]
)
PII_AustralianTaxFileNumber = regex_factory(
    **AUSTRALIAN_REGEX["australian_tax_file_number"]
)

PII_CanadianBankAccountNumber = regex_factory(
    **CANADIAN_REGEX["canadian_bank_account_number"]
)
PII_CanadianPassportNumber = regex_factory(**CANADIAN_REGEX["canadian_passport_number"])

PII_UKDriversLicenseNumber = regex_factory(**UK_REGEX["uk_drivers_license_number"])
PII_UKNationalInsuranceNumber = regex_factory(
    **UK_REGEX["uk_national_insurance_number"]
)
PII_UKUniqueTaxpayerReferenceNumber = regex_factory(
    **UK_REGEX["uk_unique_taxpayer_reference_number"]
)
PII_UK_USPassportNumber = regex_factory(**UK_REGEX["uk_us_passport_number"])

PII_USSocialSecurityNumber = regex_factory(**US_REGEX["us_social_security_number"])
PII_USIndividualTaxPayerIdentificationNumber = regex_factory(
    **US_REGEX["us_individual_tax_payer_identification_number"]
)
PII_USBankAccountNumber = regex_factory(**US_REGEX["us_bank_account_number"])
PII_UK_USPassportNumber = regex_factory(**US_REGEX["uk_us_passport_number"])


PII_Birthday_GLiNER = ner_factory(class_=PII_GLiNERFormatter, **NER_GLiNER["birthday"])
PII_Address_GLiNER = ner_factory(class_=PII_GLiNERFormatter, **NER_GLiNER["address"])
PII_Person_GLiNER = ner_factory(class_=PII_GLiNERFormatter, **NER_GLiNER["person"])
PII_Organisation_GLiNER = ner_factory(
    class_=PII_GLiNERFormatter, **NER_GLiNER["organisation"]
)
PII_Person_Flair_Large = ner_factory(
    class_=PII_Flair_Large_Formatter, **NER_FLAIR["person"]
)
PII_Organisation_Flair_Large = ner_factory(
    class_=PII_Flair_Large_Formatter, **NER_FLAIR["organisation"]
)
PII_PersonAndOrganisation_Flair_Large = ner_factory(
    class_=PII_Flair_Large_Formatter, **NER_FLAIR["person_and_organisation"]
)
PII_Person_RobBERT = ner_factory(
    class_=PII_RobBERT_V2_Dutch_Formatter, **NER_RobBERT["person"]
)
PII_Organisation_RobBERT = ner_factory(
    class_=PII_RobBERT_V2_Dutch_Formatter, **NER_RobBERT["organisation"]
)
PII_PersonAndOrganisation_RobBERT = ner_factory(
    class_=PII_RobBERT_V2_Dutch_Formatter, **NER_RobBERT["person_and_organisation"]
)
PII_Person_XLM_RoBERTa = ner_factory(
    class_=PII_XLM_RoBERTa_Dutch_Formatter, **NER_XLM_RoBERTa["person"]
)
PII_Organisation_XLM_RoBERTa = ner_factory(
    class_=PII_XLM_RoBERTa_Dutch_Formatter, **NER_XLM_RoBERTa["organisation"]
)
PII_PersonAndOrganisation_XLM_RoBERTa = ner_factory(
    class_=PII_XLM_RoBERTa_Dutch_Formatter, **NER_XLM_RoBERTa["person_and_organisation"]
)

PII_Grouped_Dutch_Person = ner_factory(
    class_=PII_XLM_RoBERTa_Dutch_Formatter, **NER_XLM_RoBERTa["person"], group=True
)
PII_Dutch_Organisation = ner_factory(
    class_=PII_XLM_RoBERTa_Dutch_Formatter, **NER_XLM_RoBERTa["organisation"]
)
PII_Grouped_English_Person = ner_factory(
    class_=PII_Flair_Large_Formatter, **NER_FLAIR["person"], group=True
)
PII_English_Organisation = ner_factory(
    class_=PII_Flair_Large_Formatter, **NER_FLAIR["organisation"]
)


PII_Computer = chain_factory(
    ordered_list_of_formatter_classes=[
        PII_EmailAddress,
        PII_IPAddress,
        PII_URL,
        PII_MACAddress,
        PII_FilePath,
    ]
)
PII_Banking = chain_factory(
    ordered_list_of_formatter_classes=[
        PII_CreditCardNumber,
        PII_IBAN,
        PII_EuropeanVATNumber,
        PII_CreditCardCVVCode,
        PII_CreditCardExpiryDate,
    ]
)
PII_Common = chain_factory(
    ordered_list_of_formatter_classes=[
        PII_InternationalPhoneNumber,
    ]
)
PII_Dutch = chain_factory(
    ordered_list_of_formatter_classes=[
        PII_DutchLicensePlateNumber,
        PII_DutchPhoneNumber,
        PII_DutchIdentityNumberBSN,
        PII_DutchIdentityDocumentNumber,
        PII_DutchVreemdelingenDocumentNumber,
        PII_DutchBelgianDriversLicenseNumber,
        PII_Grouped_Dutch_Person,
        PII_Dutch_Organisation,
    ]
)
PII_Belgian = chain_factory(
    ordered_list_of_formatter_classes=[
        PII_BelgianIdentityNumber,
        PII_BelgianLicencePlateNumber,
        PII_BelgianPhoneNumber,
        PII_BelgianPassportNumber,
        PII_DutchBelgianDriversLicenseNumber,
    ]
)
PII_Australian = chain_factory(
    ordered_list_of_formatter_classes=[
        PII_AustralianDriversLicenseNumber,
        PII_AustralianBankAccountNumber,
        PII_AustralianPassportNumber,
        PII_AustralianTaxFileNumber,
    ]
)
PII_Canadian = chain_factory(
    ordered_list_of_formatter_classes=[
        PII_CanadianBankAccountNumber,
        PII_CanadianPassportNumber,
    ]
)
PII_UK = chain_factory(
    ordered_list_of_formatter_classes=[
        PII_UKDriversLicenseNumber,
        PII_UKNationalInsuranceNumber,
        PII_UKUniqueTaxpayerReferenceNumber,
        PII_UK_USPassportNumber,
    ]
)
PII_US = chain_factory(
    ordered_list_of_formatter_classes=[
        PII_USSocialSecurityNumber,
        PII_USIndividualTaxPayerIdentificationNumber,
        PII_USBankAccountNumber,
        PII_UK_USPassportNumber,
    ]
)

PII_Everything = language_factory(
    language_to_formatter_classes={
        "nl": chain_factory(
            ordered_list_of_formatter_classes=[
                # Computer
                PII_EmailAddress,
                PII_IPAddress,
                PII_URL,
                PII_EuropeanVATNumber,  # EuropeanVATNumber can be found in MACAddress tests
                PII_MACAddress,
                PII_FilePath,
                ner_factory(
                    class_=PII_XLM_RoBERTa_Dutch_Formatter,
                    **NER_XLM_RoBERTa["person_and_organisation"],
                    group=True
                ),
                # PII_Birthday_GLiNER,
                # PII_Address_GLiNER,
                # Dutch
                PII_DutchLicensePlateNumber,
                PII_IBAN,  # DutchPhoneNumber can be found in IBAN number tests
                PII_CreditCardNumber,  # DutchPhoneNumber can be found in CreditCardNumber tests
                PII_DutchIdentityNumberBSN,
                PII_DutchIdentityDocumentNumber,
                PII_DutchVreemdelingenDocumentNumber,
                # Belgian
                PII_BelgianIdentityNumber,
                PII_BelgianLicencePlateNumber,
                PII_BelgianPassportNumber,
                # Common
                PII_InternationalPhoneNumber,
                # Banking
                PII_DutchBelgianDriversLicenseNumber,  # DutchPhoneNumbers can be found in DutchBelgianDriversLicenseNumber tests
                PII_BelgianPhoneNumber,  # DutchPhoneNumber can be found in BelgianPhoneNumber tests
                PII_DutchPhoneNumber,
                ner_factory(
                    class_=PII_GLiNERFormatter,
                    entity_types=[
                        "home address",
                        "birthday",
                        "credit card cvv code",
                        "credit card expiry date",
                    ],
                    mask=[
                        "<address>",
                        "<birthday>",
                        "<credit_card_cvv_code>",
                        "<credit_card_expiry_date>",
                    ],
                    supported_languages=["nl"],
                ),
                # PII_CreditCardCVVCode,
                # PII_CreditCardExpiryDate,
            ]
        ),
        "en": chain_factory(
            ordered_list_of_formatter_classes=[
                PII_FilePath,
                ner_factory(
                    class_=PII_Flair_Large_Formatter,
                    **NER_FLAIR["person_and_organisation"],
                    group=True
                ),
                # PII_Address_GLiNER,
                # PII_Birthday_GLiNER,
                # Computer
                PII_EmailAddress,
                PII_IPAddress,
                PII_URL,
                PII_MACAddress,
                # Australian
                PII_AustralianPassportNumber,
                # Canadian
                PII_CanadianPassportNumber,
                # UK
                # PII_USBankAccountNumber,
                PII_UKDriversLicenseNumber,
                PII_UKNationalInsuranceNumber,
                PII_UKUniqueTaxpayerReferenceNumber,
                PII_UK_USPassportNumber,
                # US
                PII_USSocialSecurityNumber,
                PII_USIndividualTaxPayerIdentificationNumber,
                # Common
                PII_InternationalPhoneNumber,
                # Banking
                PII_CreditCardNumber,
                PII_IBAN,
                PII_EuropeanVATNumber,
                # PII_CreditCardCVVCode,
                # PII_CreditCardExpiryDate,
                PII_AustralianBankAccountNumber,  # PII_AustralianBankAccountNumber can be found in PII_UKUniqueTaxpayerReferenceNumber
                PII_AustralianTaxFileNumber,  # PII_AustralianTaxFileNumber can be found in PII_USBankAccountNumber tests.
                PII_CanadianBankAccountNumber,  # PII_CanadianBankAccountNumber can be found in PII_IBAN tests.
                PII_AustralianDriversLicenseNumber,  # PII_AustralianDriversLicense can be found in PII_UKNationalInsuranceNumber, PII_USBankAccountNumber, PII_AustralianPassportNumber, PII_CanadianBankAccountNumber tests.
                PII_USBankAccountNumber,
                ner_factory(
                    class_=PII_GLiNERFormatter,
                    entity_types=[
                        "home_address",
                        "birthday",
                        "credit card cvv code",
                        "credit card expiry date",
                    ],
                    mask=[
                        "<address>",
                        "<birthday>",
                        "<credit_card_cvv_code>",
                        "<credit_card_expiry_date>",
                    ],
                    supported_languages=["en"],
                ),
            ]
        ),
    }
)
