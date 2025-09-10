<div align="center">
<h1>
<a href="https://gpt-nl.nl/" target="_blank"><img src ="https://gpt-nl.nl/publish/pages/5180/beeldmerk-gpt_nl.svg" alt="GPT-NL" widht="200"></a><br>
Data Curation Modules
</h1>
</div>

This repository contains the data curation modules. Every module is isolated to its own folder. A different repository will contain the pipeline that uses the modules.

The reason for working this way is that we want to keep the data curation modules isolated, small and easy to use. The pipeline that will use the modules, we'll want to specify which version of the module we want to use (using something like `pip install gptnl_ftfy_formatter@0.1.0`). Putting both the pipeline and the modules in the same repository promotes local referencing, which in turn goes against the point of versioning.

Note a script is included that can run a set of commands in every module directory. Use by running `python run_commands_for_all_modules.py "CMD1" "CMD2" "..."`.

## Modules

The modules are integrated as plugins within the curation pipeline, which is built on HuggingFace's [Datatrove](https://github.com/huggingface/datatrove) module. Consequently, the modules adhere to the same schema as the PipelineStep class defined in Datatrove.

### C4 Filters

The filtering process applies heuristic rules inspired by the [paper](https://jmlr.org/papers/volume21/20-074/20-074.pdf), retaining only lines with terminal punctuation and at least three words, while discarding pages with fewer than five sentences or containing elements like "lorem ipsum", curly brackets, or the word "Javascript". Additional filters remove lines with excessively long words, cookie or terms-of-use mentions, and pages with offensive language (though this last step was not implemented).

### FineWeb

[Fineweb](https://huggingface.co/spaces/HuggingFaceFW/blogpost-fineweb-v1) filters are a set of heuristic rules used to clean and refine web text data for high-quality language model training. They remove lines lacking terminal punctuation, those with fewer than three words, or pages with fewer than five sentences. Additional filters exclude content with problematic keywords (e.g. "Javascript", "lorem ipsum", cookie notices), overly long words, or structural artifacts like curly brackets, ensuring cleaner and more relevant text.

### FTFY

[FTFY](https://ftfy.readthedocs.io/en/latest/) is a Python package that heuristically repairs broken Unicode text, helping developers clean up messy input caused by encoding errors or software bugs. It’s designed to turn bad Unicode into good Unicode, making your code more robust without replacing the need for Unicode-aware programming.

### Gopher Modules

Gopher filters are a set of heuristic rules designed to assess and improve the quality of textual data by removing documents that are likely noisy, unnatural, or non-linguistic. They evaluate characteristics such as word count, average word length, symbol density, presence of stop words, and structural patterns like bullet points or ellipses. These filters help ensure that only clean, natural language content is retained for downstream tasks like training language models.

### LLM Processing

This module allows you to process text through a LLM. You pick the model name and the prompt and you get back the results.

### Machine Translation

This package wraps utilities for Machine Translation, using HuggingFace models. The selected model is `google/madlad400-10b-mt`, which is a huge model that needs to be used on GPU machines.

### NordicPile

The NordicPile filters, based on the following [paper](https://arxiv.org/pdf/2303.17183), are a complementary set of heuristic rules designed to catch low-quality text features not covered by Gopher filters. They focus on structural and statistical properties of documents, such as limiting the fraction of digits, enforcing a minimum character count, and ensuring sufficient average line and word lengths. These filters help exclude overly short, numeric-heavy, or fragmented documents to improve dataset quality for language modeling.

### PII

This module detects and formats Personally Identifiable Information (PII) in text. It identifies various types of PII, such as numerical identifiers like bank accounts, phone numbers, and passports, as well as names and organisations. Furthermore, the PII module make usage of PrivateAI services to further enhance the PII identification.

### Punctuation Formatter

Normalize unicode punctuations to English punctuations in text samples.

### Quality Analysis

The quality analysis module evaluates text quality using the perplexity metric, leveraging KenLM language models to identify unnatural or low-quality content.

### Regex formatter

This module enables the application of regular expressions in the data curation pipeline.

### TNO Filters

TNO filters are a set of quality heuristics derived from the [DataJuicer framework](https://github.com/modelscope/data-juicer), aimed at evaluating the structural integrity of textual data. They focus on line-level characteristics, such as enforcing minimum and maximum line lengths and average line length thresholds, to eliminate documents that are either too sparse or excessively verbose. These filters help ensure that the retained content is well-formed and suitable for natural language processing tasks.

### ToxicLanguage Detection

Detects and filters out toxic language based on `IMSyPP/hate_speech_nl` and `tomh/toxigen_hatebert`.

### Whitespace formatter

The whitespace formatter normalizes all whitespace characters to the standard Unicode space character (U+0020).

## Installation

1. Globally install the handler for the virtual environment and dependencies, [poetry](https://python-poetry.org/docs/): `pip install poetry`
2. - If you want to work on only one module, go to the module directory and run `poetry install`, followed by an optional `poetry run post-install` if there is a post install script.
   - If you want to work on all modules, run `python run_commands_for_all_modules.py "poetry install" "poetry run post-install"` to install everything at once.

Poetry handles the virtual environment for you. As your IDE might complain about these different virtual environments, it is recommended to use a plugin to handle this. For VSCode, you can use [Python Envy](https://marketplace.visualstudio.com/items?itemName=teticio.python-envy).

## Developing modules

In the **module directory**:

- Add dependencies by running `poetry add <DEPENDENCY>`
- Format your code by running `poetry run black .` (or set your IDE to _format on save_ (recommended!))
- Test your modules by running `poetry run pytest .`
- If testing on data files, keep the data files as small as possible.
- If data files are included for testing and they're binary files, add them to Git LFS by running `git lfs track *.<FILE_EXTENSION>`
- If you need larger data or binary files, host them externally and add a post install script that downloads them (similar to [this](pii_mappers/post_install.py)).
- Make sure to install pre-commit hooks.

## Publishing modules

Every time you want to publish your module:

1. From your module directory, run `poetry run pytest .` and fix any errors thrown.
2. From your module directory, run `poetry version <NEW_VERSION>` (or update it manually in the `pyproject.toml` file). Use [semantic versioning](https://semver.org/).
3. From your module directory, run `poetry publish --build --repository tno-gptnl`

You can build without publishing by running just `poetry build`, and you can do a dry run with `poetry publish --build --dry-run`.

## Using modules

1. In the repository where you want to use the module, add this to your `pyproject.toml` (note the `/simple` suffix when comparing this URL to the URL used for publishing):

   ```toml
   [[tool.poetry.source]]
   name = "gptnl"
   url = "..."
   priority = "supplemental"
   ```

2. Make sure the credentials are correct in your `poetry.toml` file.
3. Install modules using `poetry add <MODULE> --source tno-gptnl`
