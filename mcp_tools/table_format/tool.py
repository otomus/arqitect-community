"""Format data as a text table with configurable styles."""

import json

SUPPORTED_FORMATS = ("plain", "grid", "pipe")


def run(data: str, headers: str = "", format: str = "grid") -> str:
    """Format JSON data as a text table.

    @param data: JSON array of arrays representing table rows.
    @param headers: Optional JSON array of header strings.
    @param format: Table format: plain, grid, or pipe.
    @returns: Formatted text table.
    @throws ValueError: If data is malformed or format is unsupported.
    """
    if format not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format: {format}. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )

    rows = _parse_rows(data)
    header_list = _parse_headers(headers)

    try:
        from tabulate import tabulate
        return tabulate(
            rows,
            headers=header_list if header_list else (),
            tablefmt=format,
        )
    except ImportError:
        return _fallback_table(rows, header_list, format)


def _parse_rows(data: str) -> list:
    """Parse and validate the JSON row data."""
    try:
        rows = json.loads(data)
    except json.JSONDecodeError as err:
        raise ValueError(f"Invalid JSON data: {err}")

    if not isinstance(rows, list) or not all(isinstance(r, list) for r in rows):
        raise ValueError("Data must be a JSON array of arrays")

    return rows


def _parse_headers(headers: str) -> list:
    """Parse the optional JSON headers string."""
    if not headers:
        return []

    try:
        parsed = json.loads(headers)
    except json.JSONDecodeError as err:
        raise ValueError(f"Invalid JSON headers: {err}")

    if not isinstance(parsed, list):
        raise ValueError("Headers must be a JSON array of strings")

    return parsed


def _fallback_table(rows: list, headers: list, format: str) -> str:
    """Render a table without tabulate as a fallback."""
    all_rows = [headers] + rows if headers else rows

    if not all_rows:
        return ""

    col_widths = _calculate_column_widths(all_rows)

    lines = []
    if format == "grid":
        lines.append(_grid_separator(col_widths))

    if headers:
        lines.append(_format_row(headers, col_widths, format))
        if format == "grid":
            lines.append(_grid_separator(col_widths))
        elif format == "pipe":
            lines.append(
                "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
            )

    for row in rows:
        lines.append(_format_row(row, col_widths, format))

    if format == "grid":
        lines.append(_grid_separator(col_widths))

    return "\n".join(lines)


def _calculate_column_widths(all_rows: list) -> list:
    """Calculate the maximum width for each column."""
    num_cols = max(len(row) for row in all_rows)
    widths = [0] * num_cols
    for row in all_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    return widths


def _format_row(row: list, col_widths: list, format: str) -> str:
    """Format a single row according to the table style."""
    cells = [str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)]
    if format == "plain":
        return "  ".join(cells)
    separator = " | " if format == "grid" else " | "
    prefix = "| " if format in ("grid", "pipe") else ""
    suffix = " |" if format in ("grid", "pipe") else ""
    return prefix + separator.join(cells) + suffix


def _grid_separator(col_widths: list) -> str:
    """Create a grid-style separator line."""
    return "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
