from vllm import LLM, SamplingParams


class LLMProcessing:
    prompt: str
    model_name: str
    model: LLM

    def __init__(self, model_name: str, prompt: str):
        """
        The prompt should only have a template variable called {text}
        """
        self.model_name = model_name
        self.prompt = prompt
        self.model = LLM(model_name)

    def process_texts(
        self,
        texts: list[str],
        max_tokens: int,
        temperature: float,
        use_tqdm: bool = True,
        print_prompt: bool = False,
        use_chat_template: bool = True,
        max_context_size: int = 16384,
    ):
        # cut texts that are too long
        char_max_size = (
            max_context_size // 3
        )  # leave some room for prompt and chat template, so don't do //4
        if any(len(t) > char_max_size for t in texts):
            print("WARN: some texts will be trimmed because of max_context_size!")
        texts = [t[:char_max_size] for t in texts]

        # now format according to prompt
        input_texts = [self.prompt.format(text=text) for text in texts]
        if print_prompt:
            print(input_texts)
        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if use_chat_template:
            conversations = [[{"role": "user", "content": t}] for t in input_texts]
            raw_outputs = self.model.chat(
                messages=conversations,
                sampling_params=sampling_params,
                use_tqdm=use_tqdm,
            )
        else:
            raw_outputs = self.model.generate(
                input_texts, sampling_params, use_tqdm=use_tqdm
            )
        outputs = ["".join(chunk.text for chunk in o.outputs) for o in raw_outputs]

        return outputs
