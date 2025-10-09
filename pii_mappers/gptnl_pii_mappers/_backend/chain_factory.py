from typing import Any

from .informed_formatter import InformedFormatter


class PII_ChainFormatter(InformedFormatter):
    def __init__(self, ordered_list_of_formatter_classes) -> None:
        """Initializes the PII_ChainFormatter with a list of formatter classes.

        Args:
            ordered_list_of_formatter_classes: A list of formatter classes to be instantiated.
        """
        self.formatters: list[InformedFormatter] = [
            formatter() for formatter in ordered_list_of_formatter_classes
        ]
        super().__init__()

    def format(
        self, text: str, language: str = "unknown", with_metadata: bool = False
    ) -> str | tuple[str, dict[str, Any]]:
        """Applies each formatter in the chain to the input text.

        Args:
            text: The text to be formatted.
            language: the language.
            with_metadata: whether to return metadata.

        Returns:
            The formatted text after applying all formatters in the chain.
        """
        metadata = [] if with_metadata else None

        for formatter in self.formatters:
            results = formatter.format(text, language, with_metadata)
            if with_metadata:
                new_text, pii_metadata = results
                metadata.append(pii_metadata)
            else:
                new_text = results
            text = new_text

        if not with_metadata:
            return text
        return text, metadata

    def __str__(self) -> str:
        """Returns a string representation of the formatter chain.

        Returns:
            A string indicating the chain of formatters.
        """
        return "Formatter chain:" + " -> ".join([f.name for f in self.formatters])


def pii_chain_formatter_class_factory(**kwargs) -> PII_ChainFormatter:
    """Creates a new PII chain formatter class with a dynamic configuration.

    Args:
        **kwargs: Additional attributes for initializing the formatter class.

    Returns:
        A new class inheriting from PII_ChainFormatter.
    """
    # Ensure required attributes are present
    if "ordered_list_of_formatter_classes" not in kwargs:
        raise ValueError("Should provide classes that make up the chain formatter!")

    # Define the new class dynamically
    new_class = type(
        "PII_ChainFormatter",
        (PII_ChainFormatter,),  # Inherit from PII_ChainFormatter
        {
            "name": "PII_ChainFormatter",
            "__init__": lambda self: super(type(self), self).__init__(**kwargs),
            **kwargs,  # Add other attributes from kwargs
        },
    )
    return new_class
