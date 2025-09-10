from collections.abc import Generator

import pandas as pd
from gptnl_machine_translation.long_document_translator import LongDocumentTranslator
from tqdm import tqdm


def translate_row_dict(
    row: dict, translator: LongDocumentTranslator
) -> Generator[dict, None, None]:
    source_row = {k: v for k, v in row.items() if k not in ["text"]}
    full_text = row["text"]
    for translated_text_chunk, chunk_id in translator.translate_long_text(
        long_text=full_text
    ):
        new_title = (
            source_row["title"] + chunk_id
        )  # batch_id is something like [14200:14397] indicating offset of tokens
        yield {**source_row, "text": translated_text_chunk, "title": new_title}


def translate_dataframe(
    df: pd.DataFrame, translator: LongDocumentTranslator
) -> pd.DataFrame:
    dicts = df.to_dict(orient="records")
    new_dataset = []
    for row in tqdm(dicts, desc="dataset rows"):
        for translated_dict in translate_row_dict(row, translator=translator):
            new_dataset.append(translated_dict)
    df_new = pd.DataFrame(new_dataset)
    return df_new
