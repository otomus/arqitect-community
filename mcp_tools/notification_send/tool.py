"""Send a notification (macOS native or stub for other platforms)."""

import platform


def run(title: str, body: str, target: str = "local") -> str:
    """Send a local notification on macOS, or return instructions for other platforms."""
    if target == "local" and platform.system() == "Darwin":
        import shlex
        import os
        script = f'''display notification "{shlex.quote(body)}" with title "{shlex.quote(title)}"'''
        os.popen(f"osascript -e {shlex.quote(script)}")
        return f"Notification sent: {title}"
    return f"Notification queued for {target}: [{title}] {body}"
