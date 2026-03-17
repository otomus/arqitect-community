"""Read data from a CSV file using the csv standard library."""

import csv
import json
import os


def run(file_path: str, delimiter: str = ",") -> str:
    """
    Read a CSV file and return its contents as a JSON array of arrays.

    @param file_path: Path to the CSV file to read.
    @param delimiter: Column delimiter character, defaults to comma.
    @returns: JSON string containing an array of rows.
    @throws FileNotFoundError: If the CSV file does not exist.
    """
    resolved = os.path.abspath(file_path)
    if not os.path.exists(resolved):
        raise FileNotFoundError(f"CSV file not found: {resolved}")

    rows: list[list[str]] = []
    with open(resolved, "r", encoding="utf-8", newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=delimiter)
        for row in reader:
            rows.append(row)

    if not rows:
        return "No data found in the CSV file."

    return json.dumps(rows, indent=2)
