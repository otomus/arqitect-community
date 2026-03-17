"""Check SSL/TLS certificate of a domain."""

import json
import socket
import ssl
from datetime import datetime


def run(domain: str) -> str:
    """Check SSL certificate details for a domain."""
    context = ssl.create_default_context()
    with socket.create_connection((domain, 443), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            cert = ssock.getpeercert()
    not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
    not_before = datetime.strptime(cert["notBefore"], "%b %d %H:%M:%S %Y %Z")
    days_remaining = (not_after - datetime.utcnow()).days
    return json.dumps({
        "domain": domain,
        "issuer": dict(x[0] for x in cert.get("issuer", [])),
        "subject": dict(x[0] for x in cert.get("subject", [])),
        "not_before": not_before.isoformat(),
        "not_after": not_after.isoformat(),
        "days_remaining": days_remaining,
        "san": [x[1] for x in cert.get("subjectAltName", [])],
    }, indent=2)
