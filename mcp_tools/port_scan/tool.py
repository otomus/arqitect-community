"""Check which ports are open on a host."""

import json
import socket


def _parse_ports(ports_str: str) -> list:
    """Parse port specification into a list of integers."""
    ports = []
    for part in ports_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            ports.extend(range(int(start), int(end) + 1))
        else:
            ports.append(int(part))
    return sorted(set(ports))


def run(host: str, ports: str = "22,80,443,8080,8443") -> str:
    """Scan ports on a host and return which are open."""
    port_list = _parse_ports(ports)
    results = []
    for port in port_list:
        try:
            with socket.create_connection((host, port), timeout=2):
                results.append({"port": port, "status": "open"})
        except (ConnectionRefusedError, OSError):
            results.append({"port": port, "status": "closed"})
    open_ports = [r["port"] for r in results if r["status"] == "open"]
    return json.dumps({"host": host, "open_ports": open_ports, "details": results}, indent=2)
