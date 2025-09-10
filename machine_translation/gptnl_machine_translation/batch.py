import torch


def create_batches(
    tokenized_text: torch.Tensor | str,
    chunk_size: int,
    batch_size: int,
) -> tuple[list[list[torch.Tensor | str]], list[list[str]]]:
    """Create a list of batches (non-fixed length). Long text tokenized gets splitted in pieces of chunk_size.
    Chunks are batched together with batch_size. The lists returned do NOT have the same length.

    Result:
    - List[List[torch.Tensor]]: inner list has max length=batch_size, and all the Tensors have max length chunk_size
    - List[List[str]]: identifiers of the chunks for each batch
    """
    batches = []
    offsets_ids = []
    if isinstance(tokenized_text, torch.Tensor):
        assert tokenized_text.dim() == 1  # tokens of only one text
    else:
        assert isinstance(tokenized_text, str)
    input_ids = tokenized_text
    for i in range(0, len(input_ids), chunk_size * batch_size):
        chunks = [
            input_ids[j : j + chunk_size]
            for j in range(
                i, min(i + chunk_size * batch_size, len(input_ids)), chunk_size
            )
        ]
        lengths = [len(chunk) for chunk in chunks]
        starts_relative_batch = [sum(lengths[:j]) for j in range(len(lengths))]
        starts = [el + i for el in starts_relative_batch]
        ends = [starts[j] + lengths[j] for j in range(len(lengths))]
        ids = [f"[{start}:{end}]" for start, end in zip(starts, ends)]
        offsets_ids.append(ids)
        # print("chunks lengths", [chunk.shape for chunk in chunks])
        batches.append(chunks)

    return batches, offsets_ids
