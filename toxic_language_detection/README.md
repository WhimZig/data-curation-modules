# Toxic language detection

Detects toxic language based on `IMSyPP/hate_speech_nl` and `tomh/toxigen_hatebert`.

## Description

The ToxicLanguageDetection class is a tool designed to filter out toxic language from texts in Dutch and English. It leverages transformer-based models to identify and exclude sentences that are deemed offensive or toxic.

`You have no idea what you're talking about, stupid!` is toxic and will be removed by this module.

The structure of this module is as follows:

- `./data/`: The data folder that contains test data, including synthetically generated.
- `./src/`: The source code folder of the module.
- `./tests/`: Test code folder which tests the Toxic Language using the `./data` folder.

## Usage

```python
from gptnl_toxic_language_detection import ToxicLanguageDetection

test_text = """
Toxic language can be used in everyday conversation without even realizing it. It can start small, with insults or name-calling, but it can quickly escalate into more harmful behavior if left unchecked. For example, calling someone "stupid" or saying that they "have no idea what they're talking about" may seem harmless at first, but it can lead to hurt feelings and damaged relationships over time. Being a little bitch about does not help either, you should man up and shout right back at them. It's important to be mindful of our language and the impact it can have on others.
"""

formatter = ToxicLanguageDetection()
print(formatter.format(test_text, "english"))
```

Outputs:

```
Toxic language can be used in everyday conversation without even realizing it. It can start small, with insults or name-calling, but it can quickly escalate into more harmful behavior if left unchecked. For example, calling someone "stupid" or saying that they "have no idea what they're talking about" may seem harmless at first, but it can lead to hurt feelings and damaged relationships over time. It's important to be mindful of our language and the impact it can have on others.
```

Removing the `Being a little bitch about does not help either, you should man up and shout right back at them.` from the text.

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

To run the tests for the toxic language detection module, you can use the following command: `pytest . in the main directory.
