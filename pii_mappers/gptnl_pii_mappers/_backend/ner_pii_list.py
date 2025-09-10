NER_GLiNER = {
    "birthday": {
        "entity_types": ["birthday"],
        "description": "A specific reference to a birthday of a person.",
        "mask": "<birthday>",
        "name": "PII_Birthday",
        "supported_languages": [
            "en",  # English
            "fr",  # French
            "de",  # German
            "es",  # Spanish
            "pt",  # Portuguese
            "it",  # Italian
            "sl",  # Slovenian
            "el",  # Greek
            "nl",  # Dutch
        ],
    },
    "address": {
        "entity_types": ["home address"],
        "description": "A specific reference to a generally known or personal home address.",
        "mask": "<address>",
        "name": "PII_Address",
        "supported_languages": [
            "en",  # English
            "fr",  # French
            "de",  # German
            "es",  # Spanish
            "pt",  # Portuguese
            "it",  # Italian
            "sl",  # Slovenian
            "el",  # Greek
            "nl",  # Dutch
        ],
    },
    "person": {
        "entity_types": ["person"],
        "description": "A first and/or last name of an publicly unknown or known person.",
        "mask": "<person>",
        "name": "PII_Person",
        "supported_languages": [
            "en",  # English
            "fr",  # French
            "de",  # German
            "es",  # Spanish
            "pt",  # Portuguese
            "it",  # Italian
            "sl",  # Slovenian
            "el",  # Greek
            "nl",  # Dutch
        ],
    },
    "organisation": {
        "entity_types": ["organisation"],
        "description": "A name or reference to an organization, publicly known or unknown.",
        "mask": "<organisation>",
        "name": "PII_Organisation",
        "supported_languages": [
            "en",  # English
            "fr",  # French
            "de",  # German
            "es",  # Spanish
            "pt",  # Portuguese
            "it",  # Italian
            "sl",  # Slovenian
            "el",  # Greek
            "nl",  # Dutch
        ],
    },
}

NER_FLAIR = {
    "person": {
        "entity_types": "PER",
        "mask": "<person>",
        "name": "PII_Person",
        "supported_languages": ["nl", "en"],
    },
    "organisation": {
        "entity_types": "ORG",
        "mask": "<organisation>",
        "name": "PII_Organisation",
        "supported_languages": ["nl", "en"],
    },
    "person_and_organisation": {
        "entity_types": ["PER", "ORG"],
        "mask": ["<person>", "<organisation>"],
        "name": "PII_PersonAndOrganisation",
        "supported_languages": ["nl", "en"],
    },
}

NER_RobBERT = {
    "person": {
        "entity_types": "PER",
        "mask": "<person>",
        "name": "PII_Person",
        "supported_languages": ["nl"],
    },
    "organisation": {
        "entity_types": "ORG",
        "mask": "<organisation>",
        "name": "PII_Organisation",
        "supported_languages": ["nl"],
    },
    "person_and_organisation": {
        "entity_types": ["PER", "ORG"],
        "mask": ["<person>", "<organisation>"],
        "name": "PII_PersonAndOrganisation",
        "supported_languages": ["nl"],
    },
}

NER_XLM_RoBERTa = {
    "person": {
        "entity_types": "PER",
        "mask": "<person>",
        "name": "PII_Person",
        "supported_languages": ["nl"],
    },
    "organisation": {
        "entity_types": "ORG",
        "mask": "<organisation>",
        "name": "PII_Organisation",
        "supported_languages": ["nl"],
    },
    "person_and_organisation": {
        "entity_types": ["PER", "ORG"],
        "mask": ["<person>", "<organisation>"],
        "name": "PII_PersonAndOrganisation",
        "supported_languages": ["nl"],
    },
}


NER_NAME_TO_MASK = {}


# Function to update the NAME_TO_MASK dictionary
def add_to_name_to_mask(ner_dict):
    for entry in ner_dict.values():
        name = entry.get("name")
        mask = entry.get("mask")
        if isinstance(name, str) and isinstance(mask, str):
            NER_NAME_TO_MASK[name] = mask


# Update NAME_TO_MASK with all the NER datasets
for ner_dict in [NER_GLiNER, NER_FLAIR, NER_RobBERT, NER_XLM_RoBERTa]:
    add_to_name_to_mask(ner_dict)


def _print_classes_for_pii_ner():
    # To create classes in the __init__ class
    for ner_key, ner_info in NER_GLiNER.items():
        print(
            f"{ner_info['name']}_GLiNER",
            f"= ner_factory(class_=PII_GLiNERFormatter, **NER_GLiNER['{ner_key}'])",
        )

    for ner_key, ner_info in NER_FLAIR.items():
        print(
            f"{ner_info['name']}_Flair_Large",
            f"= ner_factory(class_=PII_Flair_Large_Formatter, **NER_FLAIR['{ner_key}'])",
        )

    for ner_key, ner_info in NER_RobBERT.items():
        print(
            f"{ner_info['name']}_RobBERT",
            f"= ner_factory(class_=PII_RobBERT_V2_Dutch_Formatter, **NER_RobBERT['{ner_key}'])",
        )

    for ner_key, ner_info in NER_XLM_RoBERTa.items():
        print(
            f"{ner_info['name']}_XLM_RoBERTa",
            f"= ner_factory(class_=PII_XLM_RoBERTa_Dutch_Formatter, **NER_XLM_RoBERTa['{ner_key}'])",
        )
