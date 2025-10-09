from pathlib import Path

import pandas as pd


class PublicFigureChecker:
    _instance = None

    def __new__(cls, *file_paths):
        """Singleton pattern ensuring only one instance is created,
        and reused across the codebase.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(file_paths)
        return cls._instance

    def _initialize(self, file_paths):
        self.public_figures_set = set()
        for file_path in file_paths:
            self.public_figures_set.update(self.load_names(file_path))

    @staticmethod
    def load_names(file_path):
        print(f"Loading names from file_path: {file_path}")
        names_df = pd.read_csv(
            file_path, sep=";", usecols=["label", "aliases"], dtype=str
        )
        labels = names_df["label"].dropna().tolist()
        aliases = [
            alias.strip()
            for sublist in names_df["aliases"].dropna()
            for alias in sublist.split(";")
        ]
        all_names = labels + aliases
        return {name.strip() for name in all_names}

    def is_full_name_match(self, test_string):
        return test_string.strip() in self.public_figures_set
