# LLM Processing

This module allows you to process text through a LLM. You pick the model name and the prompt and you get back the results.

## Usage

The prompts support the following template variables:
- `text`: the input text

Example:

```python
from gptnl_llm_processing.model import LLMProcessing

prompt = """Summarize the following text: {text}

Summary:
"""

model = LLMProcessing(model_name=model_name, prompt=prompt)
outputs = model.process_texts(texts=inputs, max_tokens=200, temperature=0.1)
```

## Parameters

- `model_name` (init): model to use
- `prompt` (init): prompt to use
- `max_tokens`: maximum number of tokens to generate. If not provided, will be estimated from longest input: `max(len(el) for el in inputs) / 3`
- `temperature`: temperature for the LLM

## Useful commands

### Using shared HF_HOME

```bash
export HF_HOME=/projects/prjs0986/.hf_cache_dir
```

### Snellius and vLLM + flashinfer-python

If you get: `OSError: CUDA_HOME environment variable is not set. Please set it to your CUDA install root.`

Then run:
```bash
module load 2024 CUDA/12.6.0
export CUDA_HOME=/sw/arch/RHEL9/EB_production/2024/software/CUDA/12.6.0/
```
