"""Read sleep tracking data from a configured device."""


def run(device_id: str = "", date: str = "") -> str:
    """Read sleep data from a sleep tracker device."""
    raise RuntimeError(
        "Sleep tracker requires Eight Sleep or similar device configuration. "
        "Set ARQITECT_SLEEP_TRACKER_API env var."
    )
