from collections.abc import Generator
from typing import Any, Literal

import torch
from gptnl_machine_translation.batch import create_batches
from gptnl_machine_translation.model import TranslatorModel
from tqdm import tqdm


class LongDocumentTranslator(TranslatorModel):
    def __init__(
        self,
        model_name: str = "google/madlad400-10b-mt",
        use_vllm: bool = True,
        chunk_mode: Literal["characters", "tokens"] = "characters",
        chunk_size: int = 200,
        batch_size: int = 128,
        batch_stop_at: int | None = None,
        dry_run: bool = False,
        source_language: str | None = None,
        destination_language: str = "Dutch",
        **kwargs: dict[str, Any],
    ):
        """Args:
        - `model_name` is the HuggingFace model name.
        - `use_vllm` configures whether to use vLLM for faster inference (only works with LLM models, not with traditional machine translation e.g. madlab)
        - `chunk_mode` configures whether the chunking is done based on characters or on tokens.
        - `chunk_size` is the max length that the translation model can handle, counted in `chunk_mode` (tokens or characters, usually 4 char for 1 token but can vary).
        - `batch_size` is how many text the model can translate in parallel.
        - `batch_stop_at` is to early terminate with a reduced number of batches (debug only).
        - `dry_run` is to skip translation (debug only, useful to see the total number of batches).
        """
        self.model_name = model_name
        self.use_vllm = use_vllm
        self.chunk_mode = chunk_mode
        self.chunk_size = chunk_size
        if self.use_vllm and self.chunk_mode == "tokens":
            raise NotImplementedError(
                f"self.use_vllm={self.use_vllm} and self.chunk_mode={self.chunk_mode} is not supported (model)"
            )
        self.batch_size = batch_size
        self.batch_stop_at = batch_stop_at
        self.dry_run = dry_run
        super().__init__(
            model_name=model_name,
            disable_model_load=self.dry_run,
            source_language=source_language,
            destination_language=destination_language,
            use_vllm=use_vllm,
            **kwargs,
        )

    def translate_long_text(
        self, long_text: str
    ) -> Generator[tuple[str, str, str], None, None]:
        cleaned_text = long_text.replace(
            "\n", " "
        )  # Madlad doesn't deal well with newlines
        if self.chunk_mode == "characters":
            batches, offsets_ids = create_batches(
                cleaned_text,
                chunk_size=self.chunk_size,  # TODO: adjust?
                batch_size=self.batch_size,
            )
            source_texts: list[list[str]] = batches  # type: ignore
        elif self.chunk_mode == "tokens":
            tokenized_text = self.tokenize(cleaned_text)
            assert tokenized_text.dim() == 2
            assert tokenized_text.shape[0] == 1  # only one text
            tokenized_text = tokenized_text[0]
            assert tokenized_text.dim() == 1
            batches, offsets_ids = create_batches(
                tokenized_text,
                chunk_size=self.chunk_size,
                batch_size=self.batch_size,
            )
            source_texts: list[list[str]] = [
                self.tokenizer.batch_decode(inputs) for inputs in batches
            ]
        else:
            raise ValueError(f"self.chunk_mode={self.chunk_mode}")
        # Process the text in batches
        for i, inputs in enumerate(
            tqdm(batches, desc="LongDocumentTranslator::batches")
        ):
            assert isinstance(inputs, list)
            if self.batch_stop_at and i >= self.batch_stop_at:
                print(f"early stopping with batch_stop_at={self.batch_stop_at}")
                break
            if self.dry_run:
                chunk_translated_text = source_texts[i]
            else:
                if self.chunk_mode == "characters":
                    assert isinstance(inputs[0], str)
                    inputs_str: list[str] = inputs  # type: ignore
                    chunk_translated_text = self.translate_texts(
                        texts=inputs_str,
                    )
                elif self.chunk_mode == "tokens":
                    assert isinstance(inputs[0], torch.Tensor)
                    assert inputs[0].dim() == 1
                    inputs_tensors: list[torch.Tensor] = inputs  # type: ignore
                    chunk_translated_text = self.translate_tokens(
                        inputs_tensors,
                    )
            offset_ids = offsets_ids[i]
            # source_token = source_tokens[i]
            for j, translated_text in enumerate(chunk_translated_text):
                offset_id = offset_ids[j]
                source_text = source_texts[i][j]
                yield translated_text, offset_id, source_text
