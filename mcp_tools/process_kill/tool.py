"""Kill a process by PID with a specified signal."""

import os
import signal as signal_module


SUPPORTED_SIGNALS = {
    "TERM": signal_module.SIGTERM,
    "KILL": signal_module.SIGKILL,
    "HUP": signal_module.SIGHUP,
    "INT": signal_module.SIGINT,
    "USR1": signal_module.SIGUSR1,
    "USR2": signal_module.SIGUSR2,
}


def run(pid: int, signal: str = "TERM") -> str:
    """
    Send a signal to a process identified by PID.

    @param pid: Process ID to send the signal to.
    @param signal: Signal name (e.g. 'TERM', 'KILL', 'HUP'). Defaults to 'TERM'.
    @returns: Confirmation message.
    @throws ValueError: If the signal name is not recognized.
    @throws ProcessLookupError: If no process with the given PID exists.
    @throws PermissionError: If insufficient permissions to signal the process.
    """
    signal_upper = signal.upper()

    if signal_upper not in SUPPORTED_SIGNALS:
        supported = ", ".join(sorted(SUPPORTED_SIGNALS.keys()))
        raise ValueError(
            f"Unsupported signal '{signal}'. Supported signals: {supported}"
        )

    sig = SUPPORTED_SIGNALS[signal_upper]
    os.kill(pid, sig)

    return f"Signal {signal_upper} sent to process {pid}"
