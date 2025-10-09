from collections.abc import Callable

from .informed_formatter import InformedFormatter, PIISmartReplacerAndCounter


class PII_RegexFormatter(InformedFormatter):
    """Checkes whether .... adhers the logic defined in the validation function and then replaces .... in the document text.

    Args:
        remove_example: Whether to replace.
        example_replacement: tuple of strings to use as replacement. They will be used in a circular way.
        regex_expression: Regular expression to use for identifying PII.
        mask: Replacement mask for found matches.
    """

    name = "Regex PII"

    def __init__(
        self,
        pattern: str,
        mask: str = "<example>",
        validator: Callable[[str], bool] | None = None,
        keywords: list[str] | None = None,
        keyword_range: int | None = None,
        **kwargs,
    ):
        super().__init__()
        self.pattern = pattern
        self.mask = mask
        self.remove_example = True
        self.validator = validator
        self.keywords = keywords
        self.keyword_range = keyword_range
        self.replacer = PIISmartReplacerAndCounter(
            self.pattern,
            self.mask,
            self.validator,  # Can be None
            self.keywords,  # Can be None
            self.keyword_range,  # Can be None
        )
        if validator:
            self.name = f"Validated {self.name}"

        if self.keywords and self.keyword_range:
            self.name = f"Smart {self.name}"

        # Store additional keyword arguments as instance attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def format(
        self, text: str, language: str = "unknown", with_metadata=False
    ) -> str | tuple[str, dict]:
        if self.remove_example:
            text, count = self.replacer.replace(text)
        if not with_metadata:
            return text
        return text, {
            "entity_types": [self.name.replace("PII_", "")],
            "entity_type_counts": [count],
            "masks": [self.mask],
            "mask_counts": [count],
        }


def pii_regex_formatter_class_factory(**kwargs) -> PII_RegexFormatter:
    """A class factory that creates a new PII validated regex formatter class with a dynamic configuration.

    Args:
        name: Name for the new class.
        **kwargs: Additional dynamic attributes for initializing the formatter class such as
                  pattern, mask, description, source, etc.

    Returns:
        A new class that inherits from PII_RegexFormatter with specified configuration.
    """
    # Ensure required attributes are present
    if "pattern" not in kwargs or "mask" not in kwargs:
        raise ValueError("Both 'pattern', 'mask', and must be provided in kwargs.")

    class_name = f"PII_{'Validated' if 'validator' in kwargs else ''}RegexFormatter"
    # Also requires name argument in factory function which seemed unnecessary.
    # Define the new class dynamically
    new_class = type(
        class_name,
        (PII_RegexFormatter,),  # Inherit from PII_RegexFormatter
        {
            "name": class_name,
            "__init__": lambda self: super(type(self), self).__init__(**kwargs),
            **kwargs,  # Add other attributes from kwargs
        },
    )
    return new_class
