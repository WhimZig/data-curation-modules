import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BatchEncoding,
    MarianMTModel,
    MarianTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
    PreTrainedTokenizerFast,
    T5ForConditionalGeneration,
    T5Tokenizer,
)
from vllm import LLM, SamplingParams


class TranslatorModel:
    tokenizer: PreTrainedTokenizer | PreTrainedTokenizerFast
    model: PreTrainedModel | None = None
    vllm_model: LLM | None = None
    target_indicator: str
    model_name: str
    disable_model_load: bool

    def __init__(
        self,
        model_name: str = "google/madlad400-10b-mt",
        disable_model_load: bool = False,
        source_language: str | None = None,
        destination_language: str = "Dutch",
        use_vllm: bool = True,
    ):
        self.model_name = model_name
        self.disable_model_load = disable_model_load
        self.use_vllm = use_vllm
        if self.use_vllm:
            self.vllm_model = LLM(model_name)
        else:
            if "opus" in model_name:
                self.tokenizer = MarianTokenizer.from_pretrained(model_name)
                if not self.disable_model_load:
                    self.model = MarianMTModel.from_pretrained(model_name)
                else:
                    self.model = None
            elif "GemmaX2" in model_name:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                if not self.disable_model_load:
                    self.model = AutoModelForCausalLM.from_pretrained(
                        model_name, device_map="auto"
                    )
                else:
                    self.model = None
            else:
                self.tokenizer = T5Tokenizer.from_pretrained(model_name)
                if not self.disable_model_load:
                    self.model = T5ForConditionalGeneration.from_pretrained(
                        model_name, device_map="auto"
                    )
                else:
                    self.model = None
            self.device = torch.device("cpu")
            if self.model is not None:
                if self.model is not MarianMTModel:
                    self.device = self.model.device

        self.source_language = source_language
        self.destination_language = destination_language

        self.set_prompt_template()
        # self.target_token = self.tokenize(self.target_indicator)

    def set_prompt_template(self):
        """Get the prompt for the model. Available variables are:
        - `source_language`: the source language
        - `destination_language`: the destination language"""
        self.destination_language_short = None
        if "bible" in self.model_name:
            self.destination_language_short = {"dutch": "nld"}[
                self.destination_language.lower()
            ]
            self.prompt_template_prefix = ""
            self.prompt_template_suffix = f">>{self.destination_language_short}<<"
        elif "opus" in self.model_name:
            self.prompt_template = ""
            self.prompt_template_suffix = ""
        elif "madlad" in self.model_name:
            self.destination_language_short = {"dutch": "nl"}[
                self.destination_language.lower()
            ]
            self.prompt_template_prefix = ""
            self.prompt_template_suffix = f"<2{self.destination_language_short}> "
        elif "GemmaX2" in self.model_name:
            self.prompt_template_prefix = f"Translate this from {self.source_language} to {self.destination_language}:\n{self.source_language}:"
            self.prompt_template_suffix = f"\n{self.destination_language}:"
        else:
            raise ValueError(f"unknown prompts for model {self.model_name}")

        if not self.use_vllm:
            self.tokens_prefix = self.tokenize(self.prompt_template_prefix)[0]
            self.tokens_suffix = self.tokenize(self.prompt_template_suffix)[0]

    def tokenize(self, text: str | list[str]) -> torch.Tensor:
        return self.tokenizer(text, return_tensors="pt", padding=True).input_ids.to(
            self.device
        )

    def translate_texts(
        self, texts: list[str], max_length: int | None = None
    ) -> list[str]:
        # tokenize separately so that the attention_mask can be built properly in the self.translate_tokens based on lengths
        if self.use_vllm:
            if not max_length:
                # 1.2 margin to change language
                # /3 from chars to tokens (conservative)
                max_length = int((max(len(el) for el in texts) * 1.2) // 3)
            prompts = [
                self.prompt_template_prefix + t + self.prompt_template_suffix
                for t in texts
            ]
            sampling_params = SamplingParams(
                max_tokens=max_length,
            )
            outputs = self.vllm_model.generate(prompts, sampling_params)
            results = []
            for output in outputs:
                prompt = output.prompt
                # print("len(output.outputs)", len(output.outputs))
                generated_text = output.outputs[0].text
                # print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")
                results.append(generated_text)
            return results
        else:
            tokens_input = [self.tokenize(text)[0] for text in texts]
            decoded_texts = self.translate_tokens(tokens_input, max_length=max_length)
            return decoded_texts

    def translate_tokens(
        self,
        tokens_input: list[torch.Tensor],
        max_length: int | None = None,
    ) -> list[str]:
        # print(self.tokens_prefix.shape)
        # print(tokens_input[0].shape)
        # first concatenate with prefix and suffix
        tokens_with_target = [
            torch.cat(
                [
                    self.tokens_prefix,  # .squeeze(0).to("cpu"),
                    token_input,  # .to("cpu"),
                    self.tokens_suffix,  # .squeeze(0).to("cpu"),
                ]
            )
            for token_input in tokens_input
        ]
        # print([el.shape for el in tokens_with_target])
        # now pad to make single shape
        placeholder_attention_mask = [
            torch.ones(chunk.shape) for chunk in tokens_with_target
        ]
        padded_tokens_with_target: BatchEncoding = self.tokenizer.pad(
            encoded_inputs=BatchEncoding(
                data={
                    "input_ids": tokens_with_target,
                    "attention_mask": placeholder_attention_mask,
                }
            ),
            padding_side="left",
            padding=True,
        )
        # print(padded_tokens_with_target)
        if not max_length:
            max_length = padded_tokens_with_target.input_ids.shape[1]
        assert isinstance(max_length, int)
        tokens_input_f: torch.Tensor = padded_tokens_with_target.input_ids.to(
            self.device
        )
        attention_mask: torch.Tensor = padded_tokens_with_target.attention_mask.to(
            self.device
        )
        translated = self._generate(
            tokens_input=tokens_input_f,
            max_length=max_length,
            attention_mask=attention_mask,
        )
        # if the model is a LLM, it will also provide back the input tokens
        # here we check if the input tokens are found or not
        if translated.shape[1] > tokens_input_f.shape[1] and torch.equal(
            tokens_input_f, translated[:, : tokens_input_f.shape[1]]
        ):
            # remove the input tokens
            translated = translated[:, tokens_input_f.shape[1] :]
        return self._decode(translated)

    def _generate(
        self,
        tokens_input: torch.Tensor,
        max_length=512,
        attention_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if not self.model:
            raise ValueError("self.model not set")
        if attention_mask is not None:
            # print(tokens_input.shape, tokens_input.device)
            # print(attention_mask.shape, attention_mask.device)
            translated = self.model.generate(
                input_ids=tokens_input,
                max_new_tokens=max_length,
                attention_mask=attention_mask,
            )
        else:
            translated = self.model.generate(
                input_ids=tokens_input, max_new_tokens=max_length
            )
        assert isinstance(translated, torch.Tensor)
        return translated

    def _decode(self, translated: torch.Tensor) -> list[str]:
        return self.tokenizer.batch_decode(translated, skip_special_tokens=True)
