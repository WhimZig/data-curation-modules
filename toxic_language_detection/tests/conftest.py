# conftest.py
from collections import defaultdict

import pandas as pd
import pytest

results_by_module = defaultdict(lambda: {"true": [], "pred": []})
output_file_dictionary = None

# Constants for readability
EXPECTED_LABEL_FORMATTED = 1
EXPECTED_LABEL_UNCHANGED = 0
SELECT_N_SAMPLES = 11


def evaluate_formatting(
    expected_label: str, sentence: str, formatted_sentence: str, toxic_bit: str
) -> str:
    """Evaluates the correctness of PII formatting in a given sentence.

    Args:
        expected_label (str): The expected label indicating whether a formatting
            change is necessary. If `expected_label` is `EXPECTED_LABEL_FORMATTED`,
            a change is expected.
        sentence (str): The original sentence that may or may not be formatted.
        formatted_sentence (str): The sentence after attempted PII formatting.
        entity (str): The PII entity in the sentence that should be affected by formatting.
        mask (str): The mask that should be present in the formatted sentence, if expected_label == 1.

    Returns:
        str: 'pass' if formatting is correct; otherwise, explains the reason for failure.
    """
    if expected_label == EXPECTED_LABEL_FORMATTED:
        if toxic_bit not in sentence:
            return (
                0,
                f"The toxic bit '{toxic_bit}' was expected to be in the sentence '{sentence}'. Please update the test dataset if necessary.",
            )
        if toxic_bit in formatted_sentence:
            return (
                0,
                f"Expected the toxic bit '{toxic_bit}' to be removed in the formatted sentence, but it was found in: '{formatted_sentence}'.",
            )
        return 1, "pass"
    else:
        if formatted_sentence != sentence:
            return (
                1,
                f"No formatting was expected, but a change was detected. Original: '{sentence}', Formatted: '{formatted_sentence}'.",
            )
        return 0, "pass"


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Collect expected and predicted values after each test."""
    if call.when == "call":  # Only add successful test cases
        expected = dict(item.user_properties).get("expected")
        predicted = dict(item.user_properties).get("predicted")
        if expected is not None and predicted is not None:
            module_name = item.module.__name__
            results_by_module[module_name]["true"].append(expected)
            results_by_module[module_name]["pred"].append(predicted)

        # Logic for outputting larger csv file of all tests
        global output_file_dictionary
        if output_file_dictionary is None:
            output_file_dictionary = defaultdict(list, {"name": []})

        for key, value in dict(item.user_properties).items():
            if key not in output_file_dictionary:
                for _ in range(len(output_file_dictionary["name"]) - 1):
                    output_file_dictionary[key].append("")

            output_file_dictionary[key].append(value)


def calculate_metrics(true_labels, predicted_labels):
    """Calculate precision, recall, F1 score, and confusion matrix values."""
    tp = sum(
        1
        for t, p in zip(true_labels, predicted_labels, strict=False)
        if t == 1 and p == 1
    )
    fp = sum(
        1
        for t, p in zip(true_labels, predicted_labels, strict=False)
        if t == 0 and p == 1
    )
    tn = sum(
        1
        for t, p in zip(true_labels, predicted_labels, strict=False)
        if t == 0 and p == 0
    )
    fn = sum(
        1
        for t, p in zip(true_labels, predicted_labels, strict=False)
        if t == 1 and p == 0
    )

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0
    )
    ratio = sum(true_labels) / len(true_labels) if len(true_labels) > 0 else 0

    return {
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "RATIO": ratio,
    }


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Calculate and display precision, recall, F1 score per test file, sorted by F1 score,
    and also show TP, FP, TN, FN dynamically based on the dictionary keys.
    """
    if exitstatus == 4 or not output_file_dictionary:
        return

    terminalreporter.write_sep("=", "Custom Final Report")
    results_with_scores = []

    # Collect metrics for each module
    for module_name, result in results_by_module.items():
        if result["true"] and result["pred"]:
            # Calculate metrics manually
            test_info = calculate_metrics(result["true"], result["pred"])
            results_with_scores.append((module_name, test_info))
        else:
            # In case of missing data, append None
            results_with_scores.append((module_name, None))

    # Sort the results by F1 score (None values last)
    results_with_scores.sort(
        key=lambda x: (x[1] is None, x[1]["F1"] if x[1] else float("inf"))
    )

    # Display sorted results with dynamic key printing
    for module_name, test_info in results_with_scores:
        if test_info is not None:
            terminalreporter.write(f"\n{module_name:<65} - ")
            for key, value in test_info.items():
                # Capitalize the first letter of each key for printing
                terminalreporter.write(
                    f"{key}: {value:.2f} "
                    if isinstance(value, (int, float))
                    else f"{key}: {value} "
                )
        else:
            terminalreporter.write(
                f"\n{module_name:<65} - No results to calculate metrics."
            )

    terminalreporter.write("\n")

    output_file_df = pd.DataFrame(output_file_dictionary)
    all_test_results = config.getoption("all_test_results_file")
    output_file_df.to_csv(all_test_results, index=False, sep=";")

    terminalreporter.write(f"\nTest results written to {all_test_results}\n")


def pytest_addoption(parser):
    parser.addoption(
        "--all-test-results-file",
        action="store",
        default="tests_output/all_test_results.csv",
        help="Specify a file to write all the test results in CSV format.",
    )
