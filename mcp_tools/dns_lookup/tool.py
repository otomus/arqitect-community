"""Perform a DNS lookup for a domain."""

import json
import socket


def run(domain: str, type: str = "A") -> str:
    """Resolve a domain name to IP addresses (A records via socket)."""
    record_type = type.upper()
    if record_type not in ("A", "AAAA"):
        return json.dumps({"domain": domain, "type": record_type, "note": "Only A and AAAA supported via stdlib. Install dnspython for MX/TXT/CNAME/NS."})
    family = socket.AF_INET if record_type == "A" else socket.AF_INET6
    try:
        results = socket.getaddrinfo(domain, None, family, socket.SOCK_STREAM)
        ips = sorted(set(r[4][0] for r in results))
        return json.dumps({"domain": domain, "type": record_type, "records": ips}, indent=2)
    except socket.gaierror as e:
        raise RuntimeError(f"DNS lookup failed for {domain}: {e}")
