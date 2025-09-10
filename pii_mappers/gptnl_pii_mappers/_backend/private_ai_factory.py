import json
import os
import time
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
import websocket
from datatrove.utils.batching import batched
from loguru import logger
from privateai_client import PAIClient, request_objects

from .informed_formatter import InformedFormatter, split_text_into_chunks
from .private_ai_pii_list import SyntheticReplacementStrategies
from .public_figures import PublicFigureChecker
from .synthetic_replacement import SyntheticReplacement


class PrivateAIFormatter(InformedFormatter):
    def __init__(
        self,
        category: str,
        api_endpoint: str | list[str],
        replacement_type: str,
        entity_grouping_window: int,
        entity_types: str | list[str],
        check_public_figure: bool = False,
        record_processed_entities: bool = True,
        request_batch_size: int = 1,
        chunk_pool_workers: int = 32,
        doc_pool_workers: int = 32,
        api_endpoint_attempt_delay: int = 10,
        max_api_endpoint_attempts: int = 5,
        verbose: bool = False,
        validator: Callable[[str], bool] | None = None,
        public_figure_csv_files: list[str] | None = None,
        synthetic_replacement_strategies: dict[str, tuple] | None = None,
        synthetic_replacement_locale: str = "nl-NL",
        synthetic_replacement_chance: float = 1.0,
        **kwargs,
    ):
        super().__init__()
        self.category = category
        if isinstance(api_endpoint, list):
            self.api_endpoints = api_endpoint
        else:
            self.api_endpoints = [api_endpoint]
        self.replacement_type = replacement_type
        self.entity_grouping_window = entity_grouping_window
        self.check_public_figure = check_public_figure
        self.record_processed_entities = record_processed_entities
        self.request_batch_size = request_batch_size
        self.chunk_pool_workers = chunk_pool_workers
        self.doc_pool_workers = doc_pool_workers
        self.api_endpoint_attempt_delay = api_endpoint_attempt_delay
        self.max_api_endpoint_attempts = max_api_endpoint_attempts
        self.verbose = verbose
        if not self.check_public_figure and self.verbose:
            logger.warning("Not checking names in public figure dataset!")
        if public_figure_csv_files is None:
            self.public_figure_csv_files = [
                Path(__file__).parent / "public_figures" / "names_aliases_en.csv",
                Path(__file__).parent / "public_figures" / "names_aliases_nl.csv",
            ]
        else:
            self.public_figure_csv_files = public_figure_csv_files
        self.pf_checker = None
        self.synthetic_replacement = None
        if synthetic_replacement_strategies is None:
            self.synthetic_replacement_strategies = SyntheticReplacementStrategies
        else:
            self.synthetic_replacement_strategies = synthetic_replacement_strategies
        self.synthetic_replacement_locale = synthetic_replacement_locale
        self.synthetic_replacement_chance = synthetic_replacement_chance

        self.chunk_pool_executor = None
        self.doc_pool_executor = None

        if isinstance(entity_types, str):
            entity_types = [entity_types]
        elif not isinstance(entity_types, list):
            raise ValueError("entity_types must be a string or a list of strings.")

        self.entity_types = entity_types
        self.validator = validator

        self.supported_languages = []
        self.pai_clients = None
        for key, value in kwargs.items():
            setattr(self, key, value)

    def setup_pai_clients(self) -> None:
        """Create the PAI API client and other objects for performing
        synthetic replacements and batched PII formatting."""
        if self.synthetic_replacement is None and self.replacement_type != "SYNTHETIC":
            if self.synthetic_replacement_strategies is None:
                raise Exception(
                    "Replacement strategies required for synthetic replacement"
                )
            self.synthetic_replacement = SyntheticReplacement(
                strategies=self.synthetic_replacement_strategies,
                locale=self.synthetic_replacement_locale,
                chance=self.synthetic_replacement_chance,
            )
        if self.pf_checker is None:
            self.pf_checker = PublicFigureChecker(*self.public_figure_csv_files)
        if self.chunk_pool_executor is None:
            self.chunk_pool_executor = ThreadPoolExecutor(
                max_workers=self.chunk_pool_workers
            )
        if self.pai_clients is None:
            self.pai_clients = []
            task = int(os.environ.get("SLURM_ARRAY_TASK_ID", "0"))
            for api_endpoint in self.api_endpoints:
                if "{CUDA_VISIBLE_DEVICES}" in api_endpoint:
                    for device in os.environ.get("CUDA_VISIBLE_DEVICES", "0").split(
                        ","
                    ):
                        self._setup_pai_client(
                            api_endpoint.format(CUDA_VISIBLE_DEVICES=int(device) + task)
                        )
                else:
                    self._setup_pai_client(api_endpoint)

    def _setup_pai_client(self, api_endpoint: str) -> None:
        websocket_mode = api_endpoint.startswith("wss://") or api_endpoint.startswith(
            "ws://"
        )
        if websocket_mode:
            if not api_endpoint.endswith("/ws"):
                raise Exception(
                    "Make sure to also include '/ws' at the end of the websocket endpoint!"
                )
            if self.request_batch_size > 1:
                raise Exception("Websocket only allows a single request at a time.")
            websocket_connection = websocket.WebSocket()
            websocket_connection.connect(f"{api_endpoint}")
            if self.verbose:
                logger.info(f"Websocket: {websocket_connection.ping('Hello!')}")
            self.pai_clients.append(websocket_connection)
        else:
            pai_client = PAIClient(url=api_endpoint)
            live = False
            attempts = 0
            while not live and attempts < self.max_api_endpoint_attempts:
                try:
                    live = pai_client.ping()
                except requests.exceptions.ConnectionError:
                    if attempts >= self.max_api_endpoint_attempts:
                        raise Exception(
                            f"Cannot reach PrivateAI Endpoint: {api_endpoint}!"
                        )
                if not live:
                    attempts += 1
                    time.sleep(self.api_endpoint_attempt_delay)
            self.pai_clients.append(pai_client)

    def format_batch(self, batch):
        # Perform setup to avoid different threads conflicting on creating clients
        self.setup_pai_clients()
        if self.doc_pool_executor is None:
            self.doc_pool_executor = ThreadPoolExecutor(
                max_workers=self.doc_pool_workers
            )

        futures = []
        results = []
        for i, doc in enumerate(batch):
            futures.append(
                self.doc_pool_executor.submit(
                    self._format_future,
                    i,
                    doc.text,
                    with_metadata=True,
                )
            )
            results.append(None)

        for future in as_completed(futures):
            i, result = future.result()
            results[i] = result
        return results

    def _format_future(
        self, i: int, text: str, with_metadata=False
    ) -> tuple[int, str | tuple[str, dict]]:
        text, metadata = self.format_pii(text)
        if not with_metadata:
            return i, text
        return i, (text, metadata)

    def format(
        self, text: str, language: str = "unknown", with_metadata=False
    ) -> str | tuple[str, dict]:
        self.setup_pai_clients()
        text, metadata = self.format_pii(text)
        if not with_metadata:
            return text
        return text, metadata

    def format_pii(self, text):
        text_chunks = split_text_into_chunks(
            text, self.entity_grouping_window, split_type="words"
        )
        sample_entity_type_selector = request_objects.entity_type_selector_obj(
            type="ENABLE", value=self.entity_types
        )
        sample_entity_detection = request_objects.entity_detection_obj(
            entity_types=[sample_entity_type_selector]
        )

        original_chunks = []
        failed_chunks = []
        final_text = []
        entity_types = defaultdict(int)
        not_removed_entities = defaultdict(int)
        # Store count, single label and replacement
        processed_entities = defaultdict(lambda: (0, None, None))

        # Option for full batches
        futures = []
        for i, batch_chunk in enumerate(batched(text_chunks, self.request_batch_size)):
            original_chunks.append(batch_chunk)
            final_text.append("")
            futures.append(
                self.chunk_pool_executor.submit(
                    self.submit_request, i, batch_chunk, sample_entity_detection
                )
            )

        for future in as_completed(futures):
            try:
                i, response = future.result()
            except requests.exceptions.HTTPError:
                logger.exception(
                    f"HTTP error from PAI instance for chunks at index {i}\nSkipping PII for the following chunk(s):\n{original_chunks[i]}\n---"
                )
                failed_chunks.append(i)
                final_text[i] = "".join(original_chunks[i])
                continue

            name_entity_types = ["NAME", "NAME_GIVEN", "NAME_FAMILY"]

            for response_body in response:
                temp_processed_text = list(response_body["processed_text"])
                if response_body["entities_present"]:
                    for entity in response_body["entities"]:
                        start = entity["location"]["stt_idx_processed"]
                        end = entity["location"]["end_idx_processed"]
                        if (
                            self.check_public_figure
                            and entity["best_label"] in name_entity_types
                            and self.pf_checker.is_full_name_match(entity["text"])
                        ):
                            not_removed_entities[entity["text"]] += 1
                            temp_processed_text[start:end] = [entity["text"]] + [""] * (
                                end - start - 1
                            )
                        else:
                            if self.replacement_type == "SYNTHETIC":
                                replacement = entity["processed_text"]
                            else:
                                replacement = processed_entities[
                                    entity["processed_text"]
                                ][2]
                                if replacement is None:
                                    replacement = self.synthetic_replacement.replace(
                                        entity["best_label"]
                                    )
                                temp_processed_text[start:end] = [replacement] + [
                                    ""
                                ] * (end - start - 1)

                            processed_entities[entity["processed_text"]] = (
                                processed_entities[entity["processed_text"]][0] + 1,
                                entity["best_label"],
                                replacement,
                            )
                            entity_types[entity["best_label"]] += 1

                final_text[i] += "".join(temp_processed_text)

        metadata = {}
        self._add_metadata(metadata, "entity_types", list(entity_types.keys()), "")
        self._add_metadata(
            metadata, "entity_type_counts", list(entity_types.values()), 0
        )
        self._add_metadata(metadata, "failed_chunks", failed_chunks, -1)
        self._add_metadata(
            metadata, "not_removed_entities", list(not_removed_entities.keys()), ""
        )
        self._add_metadata(
            metadata,
            "not_removed_entity_counts",
            list(not_removed_entities.values()),
            0,
        )
        self._add_metadata(
            metadata, "processed_entities", list(processed_entities.keys()), ""
        )
        self._add_metadata(
            metadata,
            "processed_entity_counts",
            [count for count, _, _ in processed_entities.values()],
            0,
        )
        self._add_metadata(
            metadata,
            "processed_entity_types",
            [label for _, label, _ in processed_entities.values()],
            "",
        )
        self._add_metadata(
            metadata,
            "processed_entity_replacements",
            [replacement for _, _, replacement in processed_entities.values()],
            "",
        )

        return "".join(final_text), metadata

    @staticmethod
    def _add_metadata(
        metadata: dict, key: str, fields: list[int] | list[str], default: int | str
    ) -> None:
        if fields:
            metadata[key] = fields
        else:
            metadata[key] = [default]

    def submit_request(
        self,
        i: int,
        batch_chunk: str | list,
        sample_entity_detection: request_objects.entity_detection_obj,
    ) -> tuple[int, list]:
        endpoint = self.api_endpoints[i % len(self.api_endpoints)]
        pai_client = self.pai_clients[i % len(self.pai_clients)]
        websocket_mode = isinstance(pai_client, websocket.WebSocket)
        if not websocket_mode and not isinstance(batch_chunk, list):
            batch_chunk = [batch_chunk]
        if websocket_mode:
            batch_chunk = batch_chunk[0]

        text_request = request_objects.process_text_obj(
            text=batch_chunk,
            link_batch=True,
            entity_detection=sample_entity_detection,
            processed_text={
                "type": self.replacement_type,
                "pattern": "[UNIQUE_NUMBERED_ENTITY_TYPE]",
                "coreference_resolution": "heuristics",
            },
        )

        if self.verbose:
            logger.info(
                f"sending request to PrivateAI - Endpoint: {endpoint} - batch index: {i}"
            )
            start_time = time.time()
        if websocket_mode:
            pai_client.send(json.dumps(text_request.to_dict()))
            response = pai_client.recv()
            logger.debug(response)
            response = [json.loads(response)]

        else:
            response = pai_client.process_text(text_request).body
        if self.verbose:
            logger.info(
                f"Response received from PrivateAI - Endpoint: {endpoint} - batch index: {i} - duration: {time.time() - start_time:.2f} seconds"
            )

        return (i, response)


def pii_privateai_formatter_class_factory(category: str, **attrs) -> type:
    """Creates a new PrivateAIFormatter subclass dynamically.

    Args:
        category (str): The category name for the formatter.
        **attrs: Additional attributes to include in the new class.

    Returns:
        type: A dynamically created subclass of the given base_class with added attributes.
    """
    # New class definition
    new_class = type(
        f"PrivateAIFormatter_{category}",
        (PrivateAIFormatter,),
        {
            "category": category,
            "__init__": lambda self, api_endpoint, validator=None, group=False, **kwargs: super(
                type(self), self
            ).__init__(
                category=category,
                api_endpoint=api_endpoint,
                validator=validator,
                group=group,
                **attrs,
                **kwargs,
            ),
            **attrs,
        },
    )
    return new_class
