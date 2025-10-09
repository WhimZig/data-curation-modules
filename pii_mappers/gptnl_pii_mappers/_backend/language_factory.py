from typing import Any

from .informed_formatter import InformedFormatter


class LanguageFormatter(InformedFormatter):
    def __init__(
        self, language_to_formatter_classes: dict[str, type[InformedFormatter]]
    ) -> None:
        """Initializes the LanguageFormatter with a mapping from language codes to formatter classes.

        Args:
            language_to_formatter_classes: A dictionary mapping language codes (e.g., 'en', 'nl')
                                           to their respective InformedFormatter classes.
        """
        self.formatters: dict[str, InformedFormatter] = {
            lang: formatter_class()
            for lang, formatter_class in language_to_formatter_classes.items()
        }
        super().__init__()

    def format(
        self, text: str, language: str = "unknown", with_metadata: bool = False
    ) -> str | tuple[str, dict[str, Any]]:
        """Applies the formatter corresponding to the given language to the input text.

        Args:
            text: The text to be formatted.
            language: The language code (e.g., 'en', 'nl'). Defaults to "unknown".
            with_metadata: Whether to return metadata. Defaults to False.

        Returns:
            The formatted text after applying the language-specific formatter.
            If with_metadata is True, also returns a dictionary containing metadata.
        """
        metadata = [] if with_metadata else None
        formatter = self.formatters.get(language)

        if formatter:
            results = formatter.format(text, language, with_metadata)
            if with_metadata:
                new_text, metadata = results
            else:
                new_text = results
            text = new_text
        elif with_metadata:
            metadata = ["No formatter available for the specified language."]

        if not with_metadata:
            return text
        return text, metadata

    def __str__(self) -> str:
        """Returns a string representation of the LanguageFormatter.

        Returns:
            A string listing the supported languages.
        """
        supported_languages = ", ".join(self.formatters.keys())
        return f"Language Formatter with supported languages: {supported_languages}"


def pii_language_formatter_class_factory(**kwargs) -> type[LanguageFormatter]:
    """Creates a new LanguageFormatter class with a dynamic configuration.

    Args:
        **kwargs: Additional attributes for initializing the formatter class.
                  Must include 'language_to_formatter_classes' as a dictionary.

    Returns:
        A new class inheriting from LanguageFormatter with the specified configuration.

    Raises:
        ValueError: If 'language_to_formatter_classes' is not provided in kwargs.
    """
    if "language_to_formatter_classes" not in kwargs:
        raise ValueError(
            "Must provide 'language_to_formatter_classes' to create a LanguageFormatter."
        )

    # Extract the language to formatter mapping
    language_to_formatter_classes = kwargs["language_to_formatter_classes"]

    # Define the new class dynamically
    new_class = type(
        "LanguageFormatter",
        (LanguageFormatter,),
        {
            "name": "LanguageFormatter",
            "__init__": lambda self: super(type(self), self).__init__(
                language_to_formatter_classes
            ),
            **kwargs,  # Include any additional attributes
        },
    )
    return new_class
