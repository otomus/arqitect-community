"""Write data to a CSV file using the csv standard library."""

import csv
import json
import os


def run(file_path: str, data: str, delimiter: str = ",") -> str:
    """
    Write a JSON array of arrays to a CSV file.

    @param file_path: Output path for the CSV file.
    @param data: JSON string containing an array of arrays, e.g. '[["Name","Age"],["Alice","30"]]'.
    @param delimiter: Column delimiter character, defaults to comma.
    @returns: Confirmation message with the output path.
    @throws ValueError: If data is not valid JSON or not an array of arrays.
    """
    try:
        rows = json.loads(data)
    except json.JSONDecodeError as err:
        raise ValueError(f"Invalid JSON data: {err}")

    if not isinstance(rows, list):
        raise ValueError("Data must be a JSON array of arrays.")

    resolved = os.path.abspath(file_path)
    parent_dir = os.path.dirname(resolved)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    with open(resolved, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=delimiter)
        for index, row in enumerate(rows):
            if not isinstance(row, list):
                raise ValueError(
                    f"Row at index {index} must be an array, got {type(row).__name__}."
                )
            writer.writerow(row)

    return f"CSV file created successfully at: {resolved}"
