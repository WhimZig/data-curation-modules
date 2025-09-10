# Machine Translation

This package wraps utilities for Machine Translation, using HuggingFace models. The selected model is `google/madlad400-10b-mt`, which is a huge model that needs to be used on GPU machines.

## System requirements
The `google/madlad400-10b-mt` model requires:
- around 50GB storage
- around 90GB VRAM (GPU)
Given these requirements, you should run it on dedicated hardware (e.g., gpu_h100 partition in snellius, where you can allocate 1GPU = 1/4 node).

## Translate long documents

To translate long documents, use the `gptnl_machine_translation.long_document_translator.LongDocumentTranslator` class which helps splitting in chunks of shorter text and batching translations. The base translator `gptnl_machine_translation.model.TranslatorModel` has issues with texts longer than 300 tokens, where it starts generating nonsense.

You can play with the `chunk_size` and `batch_size` in the following way:

```python
from machine_translation.long_document_translator import LongDocumentTranslator

translator = LongDocumentTranslator(
    batch_size=32,
    chunk_size=200,
)

full_text = "Some very long text here"

for translated_text_chunk, chunk_id in translator.translate_long_text(
    long_text=full_text
):
    print(translated_text_chunk)
```

## Pipeline step

The pipeline stage is available in `gptnl_machine_translation.pipeline.TranslatorStep`. It uses the `LongDocumentTranslator` documented above, that splits the texts in chunks of shorter text.

The `TranslatorStep` has the following parameters:
- `model_name`: default value `google/madlad400-10b-mt`
- `chunk_size`: maximum length of each chunk, default `200` (with bigger values, quality of translations drops)
- `batch_size`: how many translations can be done in batch together, default `32` (fits batch on a single H100)
- `stop_at`: for testing purposes, just translate the number of lines specified, default `None` (translates the whole input file)

```python
from datatrove.pipeline.readers import ParquetReader
from datatrove.pipeline.writers.parquet import ParquetWriter
from gptnl_machine_translation.pipeline import LongDocumentTranslator

pipeline = [
    ParquetReader(
        data_folder=str(input_folder),
        file_progress=True,
        doc_progress=True,
    ),
    TranslatorStep(
        model_name="google/madlad400-10b-mt",
        chunk_size=200,
        batch_size=32,
        stop_at=None,
    ),
    ParquetWriter(output_folder=str(output_folder)),
]
```

## Useful commands

### Using shared HF_HOME

```bash
export HF_HOME=/projects/prjs0986/.hf_cache_dir
```

### Snellius and vLLM

If you get: `OSError: CUDA_HOME environment variable is not set. Please set it to your CUDA install root.`

Then run:
```bash
module load 2024 CUDA/12.6.0
export CUDA_HOME=/sw/arch/RHEL9/EB_production/2024/software/CUDA/12.6.0/
```
