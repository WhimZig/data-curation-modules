# This is the leading file for PII REGEX Information.
# Authors: Caspar Meijer & Eliza Hobo

BANKING_REGEX = {
    "credit_card_number": {
        "pattern": r"\b(\d[ -]?){13,18}\d\b",
        "mask": "<credit_card_number>",
        "description": "This PII regex identifies a sequence of 14 to 19 digits that may include spaces or hyphens, to must also pass the Luhn test.",
        "source": "https://learn.microsoft.com/en-us/purview/sit-defn-credit-card-number",
        "name": "PII_CreditCardNumber",
    },
    "credit_card_cvv_code": {
        "pattern": r"(?<![-:])\b\d{3,4}\b(?![-:])",
        # "pattern": r"\b\d{3,4}\b",
        "mask": "<credit_card_cvv_code>",
        "description": "This PII regex identifies a credit card CVV code, which consists of any 3 to 4 numerical digits.",
        "source": "https://www.geeksforgeeks.org/how-to-validate-cvv-number-using-regular-expression/",
        "name": "PII_CreditCardCVVCode",
    },
    "credit_card_expiry_date": {
        "pattern": r"\b(0[1-9]|1[0-2])[\/-]\d{2}\b",
        "mask": "<credit_card_expiry_date>",
        "description": "This PII regex identifies a 5-character date representing a credit card's expiry date formatted as MM/YY, where MM is a valid month (01-12) and YY is any two-digit year.",
        "source": "https://www.nerdwallet.com/au/credit-cards/credit-card-expiration-date",
        "name": "PII_CreditCardExpiryDate",
    },
    "iban": {
        "pattern": r"((?:[A-Za-z]\s*){2}(?:\d\s*){2}(?:[A-Za-z]\s*){0,4}(?:\s*\d){5,29}(?=\D|$))",
        "mask": "<iban>",
        "description": "This PII regex identifies an International Bank Account Number (IBAN) that starts with two uppercase letters followed by two digits, followed by a specific format of alphanumeric character groups, and allows for optional spaces or hyphens throughout the structure.",
        "source": "From Louis Weyland",
        "name": "PII_IBAN",
    },
    "european_vat_number": {
        "pattern": r"\b(ATU[0-9]{8}|BE0[0-9]{9}|BG[0-9]{9,10}|CY[0-9]{8}L|CZ[0-9]{8,10}|DE[0-9]{9}|DK[0-9]{8}|EE[0-9]{9}|EL|GR[0-9]{9}|ES[0-9A-Z][0-9]{7}[0-9A-Z]|FI[0-9]{8}|FR[0-9A-Z]{2}[0-9]{9}|GB([0-9]{9}([0-9]{3})?|[A-Z]{2}[0-9]{3})|HU[0-9]{8}|IE[0-9]S[0-9]{5}L|IT[0-9]{11}|LT([0-9]{9}|[0-9]{12})|LU[0-9]{8}|LV[0-9]{11}|MT[0-9]{8}|(NL(\.?[0-9]){9}B(\.?[0-9]){2})|PL[0-9]{10}|PT[0-9]{9}|RO[0-9]{2,10}|SE[0-9]{12}|SI[0-9]{8}|SK[0-9]{10})\b",
        "mask": "<european_vat_number>",
        "description": "This PII regex identifies European VAT numbers from various countries, which consist of specific numeric formats that may include country code prefixes and varying lengths based on the issuing country.",
        "source": "https://www.oreilly.com/library/view/regular-expressions-cookbook/9781449327453/ch04s21.html",
        "name": "PII_EuropeanVATNumber",
    },
}

COMPUTER_REGEX = {
    "e-mail_address": {
        "pattern": r"\b[a-zA-Z0-9!#$%&'*+/= ?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-zA-Z0-9-]*[a-zA-Z0-9]:)])",
        "mask": "<e-mail_address>",
        "description": "This PII regex identifies valid email addresses, which consist of a local part that may include alphanumeric characters and special symbols, followed by an '@' symbol and a domain that can be composed of alphanumeric characters and hyphens, optionally ending with an IPv4 address enclosed in square brackets.",
        "source": "DataTrove, added capitalisation",
        "name": "PII_EmailAddress",
    },
    "ip_address": {
        "pattern": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|\b\b(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?::[0-9a-fA-F]{1,4}){1,6}|:?(?::[0-9a-fA-F]{1,4}){1,7}|::(?:ffff:(?:[0-9]{1,3}\.){3}[0-9]{1,3})|(?:[0-9a-fA-F]{1,4}:){1,5}:((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))\b",
        "mask": "<ip_address>",
        "description": "This PII regex identifies both IPv4 and IPv6 addresses, accommodating various valid formats for each type.",
        "source": "https://stackoverflow.com/questions/53497/regular-expression-that-matches-valid-ipv6-addresses",
        "name": "PII_IPAddress",
    },
    "url": {
        "pattern": r"(?i)\b("
        r"(?:[a-z][\w-]+:(?:\/{1,3}|"
        r"[a-z0-9%])|www\d{0,3}[.]|"
        r"[a-z0-9.\-]+[.][a-z]{2,4}\/)"
        r"(?:[^\s()<>]+|\(([^\s()<>]+|"
        r"(\([^\s()<>]+\)))*\))"
        r"+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|"
        r"[^\s`!()\[\]{};:\'\".,<>?«»“”‘’])"
        r")",
        "mask": "<url>",
        "description": "This PII regex identifies URLs that may include an optional protocol (http or https), an optional 'www' prefix, a domain name composed of letters, numbers, or hyphens, a top-level domain such as .com or .net, and any subsequent path or parameters.",
        "source": "-",
        "name": "PII_URL",
    },
    "mac_address": {
        # "pattern": r"\b([0-9A-Fa-f]{2}[:\.\-\s]?){5}([0-9A-Fa-f]{2})|([0-9a-fA-F]{4}[\.\:\-\s]?[0-9a-fA-F]{4}[\.\:\-\s]?[0-9a-fA-F]{4})\b",
        "pattern": r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}|(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}",
        "mask": "<mac_address>",
        "description": "This PII regex identifies a MAC address format, which can be represented as six pairs of hexadecimal digits separated by either hyphens or colons, or as three groups of four hexadecimal digits separated by dots.",
        "source": "https://www.geeksforgeeks.org/how-to-validate-mac-address-using-regular-expression/",
        "name": "PII_MACAddress",
    },
    "file_path": {
        "pattern": r'\b(?:[A-Za-z]:[\\/](?:[^<>:"|?*\\/]+[\\/]){1,}[^<>:"|?*\\/]+|/(?:[^/\s]+/){1,}[^/\s]+)\b',
        "mask": "<file_path>",
        "description": "This PII regex identifies both Windows and Linux file paths, capturing various formats including those with drive letters and different directory structures.",
        "source": "https://stackoverflow.com/questions/37747139/regex-for-windows-path",
        "name": "PII_FilePath",
    },
}

COMMON_REGEX = {
    "international_phone_number": {
        "pattern": r"\+(9[976]\d|8[987530]\d|6[987]\d|5[90]\d|42\d|3[875]\d|2[98654321]\d|9[8543210]|8[6421]|6[6543210]|5[87654321]|4[987654310]|3[9643210]|2[70]|7|1)(?:\s?\d+){1,14}\b",
        "mask": "<international_phone_number>",
        "description": "This PII regex identifies valid international phone numbers, accommodating various country codes and formats with up to 15 digits that can include optional separators and spaces.",
        "source": "https://stackoverflow.com/questions/2113908/what-regular-expression-will-match-valid-international-phone-numbers",
        "name": "PII_InternationalPhoneNumber",
    },
}

DUTCH_REGEX = {
    "dutch_license_plate_number": {
        "pattern": r"\b(?:[A-Z]{2}-\d{2}-\d{2}|\d{2}-\d{2}-[A-Z]{2}|\d{2}-[A-Z]{2}-\d{2}|[A-Z]{2}-\d{2}-[A-Z]{2}|[A-Z]{2}-[A-Z]{2}-\d{2}|\d{2}-[A-Z]{2}-[A-Z]{2}|\d{2}-[A-Z]{3}-\d|\d-[A-Z]{3}-\d{2}|[A-Z]{2}-\d{3}-[A-Z]|[A-Z]-\d{3}-[A-Z]{2}|[A-Z]{3}-\d{2}-[A-Z]|\d{3}-[A-Z]{2}-\d|\d-[A-Z]{2}-\d{3}|[A-Z]-\d{2}-[A-Z]{3}|\d{3}-[A-Z]{2}-\d)\b",
        "mask": "<dutch_license_plate_number>",
        "description": "This PII regex identifies various formats of Dutch license plate numbers, which can include combinations of letters and digits in different arrangements.",
        "source": "https://nl.wikipedia.org/wiki/Nederlands_kenteken",
        "name": "PII_DutchLicensePlateNumber",
    },
    "dutch_phone_number": {
        "pattern": r"(?<!\d)"  # Ensure the preceding character is not a digit
        r"("
        r"(?:\+316|06)[\s-]?\d{8}"  # Mobile numbers: +316XXXXXXXX or 06XXXXXXXX
        r"|(?:\(?0\d{1,2}\)?)[\s-]?\d{7}"  # Landline numbers: (0XX)XXXXXXX or 0XX-XXXXXXX
        r")"
        r"(?!\d)",  # Ensure the following character is not a digit
        # "pattern": r"\b06\s*[-\s]?\d\s*[-\s]?\d\s*[-\s]?\d\s*[-\s]?\d\s*[-\s]?\d\s*[-\s]?\d\s*[-\s]?\d\s*[-\s]?\d|\(?\d{3}\)?[-\s]?\d[-\s]?\d[-\s]?\d[-\s]?\d[-\s]?\d[-\s]?\d[-\s]?\d\b",
        "mask": "<dutch_phone_number>",
        "description": "This PII regex identifies potential Dutch phone numbers, including international formats, consisting of a leading zero followed by a variable number of digits separated by non-digit characters.",
        "source": "",
        "name": "PII_DutchPhoneNumber",
    },
    "dutch_identity_number_bsn": {
        "pattern": r"\b\d{9}\b",
        "mask": "<dutch_identity_number_bsn>",
        "description": "This PII regex identifies a Dutch Citizen Service Number (BSN), which consists of exactly nine digits with no spaces. It should also pass the 11-mod check: It works by multiplying each of the nine digits in the BSN by a specific weight, summing these products, and then checking if the total is divisible by 11. The weights are applied as follows: the first digit is multiplied by 9, the second by 8, and so on down to the eighth digit, which is multiplied by 2. The final (ninth) digit is multiplied by -1. If the sum of these products modulo 11 equals zero, the BSN passes the check and is considered valid.",
        "source": "https://learn.microsoft.com/en-us/purview/sit-defn-netherlands-citizens-service-number",
        "name": "PII_DutchIdentityNumberBSN",
    },
    "dutch_identity_document_number": {
        "pattern": r"\b[A-Za-z]{2}[A-Za-z0-9]{6}\d\b",
        "mask": "<dutch_identity_document_number>",
        "description": "This PII regex identifies Dutch identity document numbers, which consist of two letters followed by six alphanumeric characters and ending with a single digit.",
        "source": "https://www.rvig.nl/node/356",
        "name": "PII_DutchIdentityDocumentNumber",
    },
    "dutch_vreemdelingen_document_number": {
        "pattern": r"\b\d{10}\b",
        "mask": "<dutch_vreemdelingen_document_number>",
        "description": "This PII regex identifies a 10-digit number commonly found on Dutch alien residency documents.",
        "source": "https://ind.nl/nl/vreemdelingendocumenten/verblijfsdocument-model-2020#gegevens-op-verblijfsdocument-model-2020-",
        "name": "PII_DutchVreemdelingenDocumentNumber",
        "keywords": ["v-nummer", "vreemdelingendocument", "vnr"],
        "keyword_range": 300,
    },
}

BELGIAN_REGEX = {
    "belgian_identity_number": {
        "pattern": r"(\d{2}\.?\d{2}\.?\d{2})[-. ]?(\d{3})[-. ]?(\d{2})",
        "mask": "<belgian_identity_number>",
        "description": "This PII regex identifies a Belgian identity number consisting of 11 digits formatted as YY.MM.DD for the date of birth, followed by three sequential digits (odd for males, even for females) and two check digits, with optional delimiters such as dots, dashes, or spaces.",
        "source": "https://learn.microsoft.com/en-us/purview/sit-defn-belgium-national-number",
        "name": "PII_BelgianIdentityNumber",
    },
    "belgian_licence_plate_number": {
        "pattern": r"\b[A-Za-z]{3}\s?[0-9]{3}|\d-?[A-Za-z]{3}-?[0-9]{3}\b",
        "mask": "<belgian_licence_plate_number>",
        "description": "This PII regex identifies Belgian licence plates, which consist of either three letters followed by three numbers or the format '1-ABC-123'.",
        "source": "https://nl.wikipedia.org/wiki/Belgisch_kenteken",
        "name": "PII_BelgianLicencePlateNumber",
    },
    "belgian_phone_number": {
        "pattern": r"\b0\s?\d\s?\d\s?\d\s?\d\s?\d\s?\d\s?\d\s?\d\b|\b04\s?\d\s?\d\s?\d\s?\d\s?\d\s?\d\s?\d\s?\d\b",
        "mask": "<belgian_phone_number>",
        "description": "This PII regex identifies Belgian phone numbers, which consist of landline numbers with 9 digits beginning with '0' and mobile numbers with 10 digits starting with '04'.",
        "source": "https://nl.wikipedia.org/wiki/Lijst_van_Belgische_zonenummers#:~:text=6%20Externe%20links-,Vaste%20lijnen,met%20inbegrip%20van%20de%200.",
        "name": "PII_BelgianPhoneNumber",
    },
    "belgian_passport_number": {
        "pattern": r"\b[A-Za-z]{2}\d{6}\b",
        "mask": "<belgian_passport_number>",
        "description": "This PII regex identifies a Belgian passport number, which consists of two alphabetical characters followed by six numerical digits.",
        "source": "https://learn.microsoft.com/en-us/purview/sit-defn-belgium-passport-number",
        "name": "PII_BelgianPassportNumber",
    },
}

_DUTCH_BELGIAN_REGEX = {
    "dutch_belgian_drivers_license_number": {
        "pattern": r"\b\d{10}\b",
        "mask": "<dutch_belgian_drivers_license_number>",
        "description": "This PII regex identifies a Dutch driver's license number consisting of exactly 10 consecutive digits.",
        "source": "-",
        "name": "PII_DutchBelgianDriversLicenseNumber",
        "keywords": ["rijbewijs"],
        "keyword_range": 300,
    },
}
DUTCH_REGEX.update(_DUTCH_BELGIAN_REGEX)
BELGIAN_REGEX.update(_DUTCH_BELGIAN_REGEX)

AUSTRALIAN_REGEX = {
    "australian_drivers_license_number": {
        "pattern": r"(?<![-:])\b([a-zA-Z0-9]{2}[0-9]{2}[a-zA-Z0-9]{5}|[a-zA-Z]{0,2}[0-9]{4,9})\b(?![-:])",
        # "pattern": r"\b([a-zA-Z0-9]{2}[0-9]{2}[a-zA-Z0-9]{5}|[a-zA-Z]{0,2}[0-9]{4,9})\b",
        "mask": "<australian_drivers_license_number>",
        "description": "This PII regex identifies Australian driver's license numbers, which can be formatted as either a combination of letters and digits consisting of two letters or digits followed by two digits and five additional alphanumeric characters, one to two optional letters followed by four to nine digits, or as a string of nine alphanumeric characters.",
        "source": "https://learn.microsoft.com/en-us/purview/sit-defn-australia-drivers-license-number",
        "name": "PII_AustralianDriversLicenseNumber",
        "keywords": ["australian driver", "australian"],
        "keyword_range": 300,
    },
    "australian_bank_account_number": {
        "pattern": r"\b\d{6,10}\b",
        "mask": "<australian_bank_account_number>",
        "description": "This PII regex identifies Australian bank account numbers that consist of a sequence of 6 to 10 digits.",
        "source": "https://learn.microsoft.com/en-us/purview/sit-defn-australia-bank-account-number",
        "name": "PII_AustralianBankAccountNumber",
        "keywords": ["australian bank", "aus bank", "australian"],
        "keyword_range": 300,
    },
    "australian_passport_number": {
        "pattern": r"(\b[NEDFACUX]\d{7})|(P[ABCDEFUWXZ]\d{7}\b)",
        "mask": "<australian_passport_number>",
        "description": "This PII regex identifies Australian passport numbers, which can either start with one of the letters N, E, D, F, A, C, U, or X followed by seven digits, or begin with the letters PA, PB, PC, PD, PE, PF, PU, PW, PX, or PZ followed by seven digits.",
        "source": "https://learn.microsoft.com/en-us/purview/sit-defn-australia-passport-number",
        "name": "PII_AustralianPassportNumber",
        "keywords": ["australia"],
        "keyword_range": 300,
    },
    "australian_tax_file_number": {
        "pattern": r"\b\d{3}\s?\d{3}\s?\d{2,3}\b",
        "mask": "<australian_tax_file_number>",
        "description": "This PII regex identifies an Australian Tax File Number, consisting of three digits followed by an optional space, three more digits, another optional space, and concluding with two to three digits that may include a check digit.",
        "source": "https://learn.microsoft.com/en-us/purview/sit-defn-australia-tax-file-number",
        "name": "PII_AustralianTaxFileNumber",
        "keywords": [
            "australia",
            "aus",
            "tax",
            "tax file number",
            "tfn",
            "australian business number",
        ],
        "keyword_range": 300,
    },
}

CANADIAN_REGEX = {
    "canadian_bank_account_number": {
        "pattern": r"\b(?<!\d)(\d{7}|\d{12}|0\d{7}|\d{5}-\d{3})(?!\d)\b",
        # "pattern": r"\b\d{7}|\d{12}\b|\b\d{5}-\d{3}$|^0\d{8}\b",
        "mask": "<canadian_bank_account_number>",
        "description": "This PII regex identifies Canadian bank account numbers represented by either 7 or 12 digits, as well as Canadian transit numbers formatted as 5 digits followed by a hyphen and 3 additional digits, or an 8-digit number starting with a 0.",
        "source": "https://learn.microsoft.com/en-us/purview/sit-defn-canada-bank-account-number",
        "name": "PII_CanadianBankAccountNumber",
        "keywords": ["canadian", "canadian bank"],
        "keyword_range": 300,
    },
    "canadian_passport_number": {
        "pattern": r"\b[A-Z]{2}\d{6}\b",
        "mask": "<canadian_passport_number>",
        "description": "This PII regex identifies a Canadian passport number, which consists of two uppercase letters followed by a sequence of six digits.",
        "source": "https://learn.microsoft.com/en-us/purview/sit-defn-canada-passport-number",
        "name": "PII_CanadianPassportNumber",
    },
}

UK_REGEX = {
    "uk_drivers_license_number": {
        "pattern": r"\b[A-Z0-9]{5}\d[0156]\d([0][1-9]|[12]\d|3[01])\d[A-Z0-9]{3}[A-Z]{2}\b",
        "mask": "<uk_drivers_license_number>",
        "description": "This PII regex identifies a UK Driver License Number, which is a 16-character alphanumeric string, used in England, Scotland, and Wales, consisting of the first 5 characters of the surname (padded with 9s if shorter), a digit representing the decade of birth and a specific value (0, 1, 5, or 6), a one-digit number followed by a date and year digit (010–319), two initials of the first name followed by 9 if no middle name, and two randomly generated capital letters for security.",
        "source": "https://docs.trellix.com/bundle/data-loss-prevention-11.10.x-classification-definitions-reference-guide/page/GUID-18CDCFBC-AD78-41E4-A5F2-F09A250CACE5.html",
        "name": "PII_UKDriversLicenseNumber",
    },
    "uk_national_insurance_number": {
        "pattern": r"\b(?!BG|GB|NK|KN|TN|NT|ZZ)([A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-Z]) ?\d{2} ?\d{2} ?\d{2} ?[A-D]\b",
        "mask": "<uk_national_insurance_number>",
        "description": "This PII regex identifies a UK National Insurance  Number formatted as two letters followed by six digits and ending with one letter.",
        "source": "https://en.wikipedia.org/wiki/National_identification_number#United_Kingdom",
        "name": "PII_UKNationalInsuranceNumber",
    },
    "uk_unique_taxpayer_reference_number": {
        "pattern": r"\b\d{10}\b",
        "mask": "<uk_unique_taxpayer_reference_number>",
        "description": "This PII regex identifies a UK Unique Taxpayer Reference Number consisting of exactly 10 consecutive digits, which is used for tax identification purposes.",
        "source": "https://learn.microsoft.com/en-us/purview/sit-defn-uk-unique-taxpayer-reference-number",
        "name": "PII_UKUniqueTaxpayerReferenceNumber",
        "keywords": ["tax", "reference"],
        "keyword_range": 300,
    },
}

US_REGEX = {
    "us_social_security_number": {
        "pattern": r"(?:\b(?:0[1-9][0-9]|00[1-9]|[1-5][0-9]{2}|6[0-5][0-9]|66[0-5789]|7[0-2][0-9]|73[0-3]|7[56][0-9]|77[012])(?:[ \-]?)?(?:0[1-9]|[1-9][0-9])(?:[ \-]?)?(?:0[1-9][0-9]{2}|00[1-9][0-9]|000[1-9]|[1-9][0-9]{3})\b)",
        "mask": "<us_social_security_number>",
        "description": "This PII regex identifies valid US Social Security Numbers, which are structured as three digits followed by a hyphen, two digits followed by another hyphen, and four digits, while ensuring that the first three digits are neither 000, 666, nor in the range 900 to 999, and the second set of digits is not 00, and the last set cannot be all zeros.",
        "source": "https://docs.trellix.com/bundle/data-loss-prevention-11.10.x-classification-definitions-reference-guide/page/GUID-53A1050C-BB3B-4496-8299-4E62A736E43D.html",
        "name": "PII_USSocialSecurityNumber",
        "keywords": ["social security number", "ssn"],
        "keyword_range": 300,
    },
    "us_individual_tax_payer_identification_number": {
        "pattern": r"\b9[0-9]{2}[-.\s]?[7-8][0-9][-.\s]?[0-9]{4}\b",
        "mask": "<us_individual_tax_payer_identification_number>",
        "description": "This regex identifies a 9-digit number starting with '9', followed by two digits, optionally separated by spaces, hyphens, or dots, where the fourth digit is '7' or '8', and ending with four more digits, accommodating various delimiters between the number groups.",
        "source": "https://docs.trellix.com/bundle/data-loss-prevention-11.10.x-classification-definitions-reference-guide/page/GUID-1A97E18C-6693-4A54-A490-0E979E3947A4.html",
        "name": "PII_USIndividualTaxPayerIdentificationNumber",
    },
    "us_bank_account_number": {
        "pattern": r"\b\d{10,12}\b",
        "mask": "<us_bank_account_number>",
        "description": "This PII regex identifies U.S. bank account numbers consisting of 6 to 17 consecutive digits.",
        "source": "https://learn.microsoft.com/en-us/purview/sit-defn-us-bank-account-number",
        "name": "PII_USBankAccountNumber",
        "keywords": ["u.s.", "us bank", "checking account", "savings account"],
        "keyword_range": 500,
    },
}

_UK_US_REGEX = {
    "uk_us_passport_number": {
        "pattern": r"\b[A-Z\d]\d{8}\b",
        "mask": "<uk_us_passport_number>",
        "description": "This PII regex identifies UK and US passport numbers: a letter or digit followed by eight digits.",
        "source": "https://learn.microsoft.com/en-us/purview/sit-defn-us-uk-passport-number",
        "name": "PII_UK_USPassportNumber",
        "keywords": ["passport"],
        "keyword_range": 300,
    },
}

UK_REGEX.update(_UK_US_REGEX)
US_REGEX.update(_UK_US_REGEX)


ALL_CATEGORIES_PII = {
    "Computer": COMPUTER_REGEX,
    "Banking": BANKING_REGEX,
    "Common": COMMON_REGEX,
    "Dutch": DUTCH_REGEX,
    "Belgian": BELGIAN_REGEX,
    "Australian": AUSTRALIAN_REGEX,
    "Canadian": CANADIAN_REGEX,
    "UK": UK_REGEX,
    "US": US_REGEX,
}

REGEX_NAME_TO_MASK = {}
for pii_category in ALL_CATEGORIES_PII.values():
    for pii in pii_category.values():
        if isinstance(pii, dict) and "name" in pii and "mask" in pii:
            REGEX_NAME_TO_MASK[pii["name"]] = pii["mask"]


def _print_classes_for_pii_regex():
    """Prints class initializations for PII regex configurations to be used in the __init__.py of the package.

    This involves iterating over the PII categories and generating the necessary initialization statements.
    """
    for category_name, category_dict in ALL_CATEGORIES_PII.items():
        for regex_key, regex_info in category_dict.items():
            print(
                regex_info["name"],
                f"= regex_factory(**{category_name.upper()}_REGEX['{regex_key}'])",
            )
        print("")


def _print_chain_formatters():
    """Prints class initializations for PII chain formatters to be used in the __init__.py of the package.

    It constructs the formatter classes for each PII category and outputs the appropriate initialization code.
    """
    for category_name, category_dict in ALL_CATEGORIES_PII.items():
        print(
            f"PII_{category_name} = pii_chain_formatter_class_factory(ordered_list_of_formatter_classes=["
        )
        for _, regex_info in category_dict.items():
            print(f"    {regex_info['name']},")
        print("])")
