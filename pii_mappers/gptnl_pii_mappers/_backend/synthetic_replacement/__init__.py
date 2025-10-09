from collections.abc import Sequence
from functools import partial
from typing import Callable

import numpy as np
from faker import Faker
from faker.providers import credit_card, internet

_Locales = tuple[str, ...]
_ReplacementStrategy = (
    tuple[str, str]
    | tuple[str, str, str]
    | tuple[str, str, _Locales]
    | tuple[str, str, _Locales, str]
)
_ReplacementStrategies = dict[str, _ReplacementStrategy]


class SyntheticReplacement:
    DEFAULT_LOCALE = "nl_NL"

    def __init__(
        self,
        strategies: _ReplacementStrategies,
        locale: str = "nl_NL",
        chance: float = 1.00,
    ) -> None:
        self._fake = Faker()
        self._fake.add_provider(credit_card)
        self._fake.add_provider(internet)
        default_locale = Faker([self.DEFAULT_LOCALE])
        self._locales = {
            self.DEFAULT_LOCALE: default_locale,
        }
        self._preferred_locale = locale
        self._replacement = ReplacementStrategy(default_locale)
        self._strategies: dict[str, Callable[[], str]] = {}
        self._chance = chance
        for entity_type, strategy in strategies.items():
            locale_provider = []
            prefix = ""
            if len(strategy) == 4:
                class_name, function, locale_provider, prefix = strategy
            elif len(strategy) == 3:
                class_name, function, locale_provider = strategy
            elif len(strategy) == 2:
                class_name, function = strategy
            else:
                raise ValueError("Strategy must have 2 to 4 elements")

            if class_name == "Faker":
                if isinstance(locale_provider, str):
                    if prefix != "":
                        raise ValueError("Prefix not supported for provider")
                    method = getattr(self._fake, function)
                else:
                    self._add_locales(locale_provider)
                    method = partial(
                        self._select_locale, function, set(locale_provider), prefix
                    )
            elif class_name == "ReplacementStrategy":
                if len(strategy) > 2:
                    raise ValueError(
                        "ReplacementStrategy does not support locales, providers or prefixes"
                    )
                method = getattr(self._replacement, function)
            else:
                raise ValueError("Class name must be Faker or ReplacementStrategy")
            self._strategies[entity_type] = method

    def replace(self, entity_type: str) -> str:
        """
        Provide a synthetic replacement for an entity type.
        """
        if self._chance >= 1 or self._replacement.get_random() <= self._chance:
            return self._strategies[entity_type]()
        return f"[{entity_type}]"

    def _add_locales(self, locales: _Locales) -> None:
        for locale in locales:
            if locale not in self._locales:
                self._locales[locale] = Faker([locale])

    def _select_locale(self, function: str, locales: set[str], prefix: str) -> str:
        if self._preferred_locale in locales:
            fake = self._locales[self._preferred_locale]
        else:
            fake = self._locales[self.DEFAULT_LOCALE]
        method = getattr(fake, function)
        return f"{prefix}{method()}"


class ReplacementStrategy:
    """
    Provider for synthetic replacement strategies that are based on random
    number generation.
    """

    BATCH_SIZE = 1000
    LICENSE_DIGITS = 10
    HEALTHCARE_DIGITS = 9
    NUMBER_DIGITS = 8
    LATITUDE_RANGE = (50.803721015, 53.5104033474)
    LONGITUDE_RANGE = (3.31497114423, 7.09205325687)
    PASSPORT_ALPHABETICAL = "ABCDEFGHIJKLMNPQRSTUVWXYZ"
    PASSPORT_NUMERIC = "123456789"
    PASSPORT_ALPHANUMERIC = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"
    URL_TLD = ("nl", "com", "net", "org")
    URL_QUERY_PROBABILITY = 0.3
    USERNAME_NUMBER_PROBABILITY = 0.4

    def __init__(self, fake: Faker) -> None:
        self._fake = fake
        self._rng = np.random.default_rng()
        self._refill_batch()

    def _refill_batch(self) -> None:
        self._batch = self._rng.random(self.BATCH_SIZE).tolist()
        self._index = 0

    def get_random(self) -> float:
        self._index += 1
        if self._index >= len(self._batch):
            self._refill_batch()
        return self._batch[self._index]

    def _generate_digits(self, digits: int) -> str:
        rand = self.get_random()

        number = f"{int(rand * (10 ** digits)):0{digits}d}"
        return number[:digits]

    def _generate_range(self, lower: float, upper: float) -> float:
        return lower + (upper - lower) * self.get_random()

    def _sample_sequence(self, sequence: Sequence[str], count: int = 1) -> str:
        if self._index + count >= len(self._batch):
            self._refill_batch()
        return "".join(
            sequence[int(self._batch[self._index + index] * len(sequence))]
            for index in range(1, count + 1)
        )

    def license(self) -> str:
        """
        Generate a driver license number.
        """
        return self._generate_digits(self.LICENSE_DIGITS)

    def healthcare_policy(self) -> str:
        """
        Generate a healthcare policy number.
        """
        return self._generate_digits(self.HEALTHCARE_DIGITS)

    def number(self) -> str:
        """
        Generate a numerical PII that does not fall under other categories,
        for now always an 8-digit string.
        """
        return self._generate_digits(self.NUMBER_DIGITS)

    def coordinate(self) -> str:
        """
        Generate a decimal coordinate position.
        """
        latitude = self._generate_range(*self.LATITUDE_RANGE)
        longitude = self._generate_range(*self.LONGITUDE_RANGE)
        return f"{latitude}, {longitude}"

    def passport(self) -> str:
        """
        Generate a passport number according to Dutch government (RvIG).
        """

        letters = self._sample_sequence(self.PASSPORT_ALPHABETICAL, 2)
        alphanum = self._sample_sequence(self.PASSPORT_ALPHANUMERIC, 5)
        digit = self._sample_sequence(self.PASSPORT_NUMERIC, 1)
        return f"{letters}{alphanum}{digit}"

    def url(self) -> str:
        """
        Generate a URL.
        """

        tld = self._sample_sequence(self.URL_TLD)
        if self.get_random() < self.URL_QUERY_PROBABILITY:
            query = "?{}={}".format(*self._fake.words(2))
        else:
            query = ""

        return "https://{0}{1}{2}.{tld}/{3}{4}{q}".format(
            *self._fake.words(5), tld=tld, q=query
        )

    def username(self) -> str:
        """
        Generate a username.
        """

        if self.get_random() < self.USERNAME_NUMBER_PROBABILITY:
            return "".join(self._fake.words(2)) + self._generate_digits(4)
        return "".join(self._fake.words(3))
