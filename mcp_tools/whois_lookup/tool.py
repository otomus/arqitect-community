"""Look up WHOIS information for a domain."""

import socket


WHOIS_PORT = 43
WHOIS_SERVER = "whois.iana.org"
TIMEOUT = 10


def _query_whois(server: str, domain: str) -> str:
    """Query a WHOIS server."""
    with socket.create_connection((server, WHOIS_PORT), timeout=TIMEOUT) as sock:
        sock.sendall((domain + "\r\n").encode("utf-8"))
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
    return response.decode("utf-8", errors="replace")


def run(domain: str) -> str:
    """Look up WHOIS data for a domain, following referrals."""
    result = _query_whois(WHOIS_SERVER, domain)
    for line in result.splitlines():
        if line.lower().startswith("refer:"):
            referral = line.split(":", 1)[1].strip()
            if referral:
                result = _query_whois(referral, domain)
                break
    return result
