"""Read or write CSV files."""

import csv
import json
import os


def run(path: str, operation: str, data: str = "", delimiter: str = ",") -> str:
    """Read data from or write data to a CSV file.

    @param path: Path to the CSV file.
    @param operation: 'read' to extract data, 'write' to create a CSV.
    @param data: JSON array of arrays (required for write).
    @param delimiter: Column delimiter character (defaults to comma).
    @returns JSON data or confirmation message.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "read":
        return _read_csv(path, delimiter)
    if operation == "write":
        return _write_csv(path, data, delimiter)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'read' or 'write'.")


def _read_csv(file_path: str, delimiter: str) -> str:
    """Read a CSV file and return its contents as JSON."""
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


def _write_csv(file_path: str, data: str, delimiter: str) -> str:
    """Write a JSON array of arrays to a CSV file."""
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
