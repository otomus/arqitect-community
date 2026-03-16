#!/usr/bin/env python3
"""Scaffold a new external MCP server entry.

Usage:
    python scripts/create_mcp.py <name> --package <npm-package>
    python scripts/create_mcp.py <name> --package <npm-package> --auth api_key --auth-env API_KEY_VAR
    python scripts/create_mcp.py <name> --package <npm-package> --auth oauth2 --auth-provider google

Examples:
    python scripts/create_mcp.py brave_search --package brave-search-mcp --category search
    python scripts/create_mcp.py linear --package linear-mcp --auth api_key --auth-env LINEAR_API_KEY
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class McpConfig:
    """All parameters needed to scaffold an MCP server entry."""

    name: str
    package: str
    description: str = ""
    category: str = "utilities"
    auth_type: str = "none"
    auth_env: str = ""
    auth_provider: str = ""
    tools: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    author: str = ""

    @property
    def mcp_dir(self) -> str:
        """Return the absolute path to this MCP server's directory."""
        return os.path.join(REPO_ROOT, "mcps", self.name)


def create_meta(config: McpConfig) -> None:
    """Write meta.json with server metadata into the MCP directory."""
    meta = {
        "name": config.name,
        "version": "1.0.0",
        "description": config.description,
        "source": "npm",
        "package": config.package,
        "command": ["npx", "-y", config.package],
        "auth_type": config.auth_type,
        "tools": config.tools,
        "capabilities": config.capabilities,
        "category": config.category,
    }
    if config.auth_env:
        meta["auth_env"] = config.auth_env
    if config.auth_provider:
        meta["auth_provider"] = config.auth_provider
    if config.author:
        meta["author"] = {"github": config.author}

    with open(os.path.join(config.mcp_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")


def _build_auth_section(config: McpConfig) -> str:
    """Return the authentication section text for the README."""
    if config.auth_type == "api_key":
        return f"Requires an API key. Set the `{config.auth_env}` environment variable."
    if config.auth_type == "oauth2":
        return f"Requires OAuth2 authentication with {config.auth_provider}."
    return "No authentication required."


def create_readme(config: McpConfig) -> None:
    """Write README.md with setup instructions into the MCP directory."""
    auth_section = _build_auth_section(config)
    tools_section = (
        "\n".join(f"- `{t}`" for t in config.tools)
        if config.tools
        else "- Tools not yet enumerated."
    )
    caps_section = (
        " ".join(f"`{c}`" for c in config.capabilities)
        if config.capabilities
        else "N/A"
    )

    readme = f"""# {config.name}

{config.description}

## Installation

This MCP server is installed automatically by sentient-core. To use it manually:

```bash
npx -y {config.package}
```

## Authentication

{auth_section}

## Tools

{tools_section}

## Capabilities

{caps_section}
"""

    with open(os.path.join(config.mcp_dir, "README.md"), "w") as f:
        f.write(readme)


def parse_args() -> argparse.Namespace:
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser(description="Scaffold a new external MCP server entry")
    parser.add_argument("name", help="MCP server name (lowercase, underscores, e.g., brave_search)")
    parser.add_argument("--package", "-p", required=True, help="npm package name (e.g., brave-search-mcp)")
    parser.add_argument("--description", "-d", default="", help="Server description (auto-generated if empty)")
    parser.add_argument("--category", "-c", default="utilities", help="Category (e.g., search, knowledge, finance)")
    parser.add_argument("--auth", default="none", choices=["none", "api_key", "oauth2"], help="Authentication type")
    parser.add_argument("--auth-env", default="", help="Environment variable for API key (when --auth api_key)")
    parser.add_argument("--auth-provider", default="", help="OAuth2 provider (when --auth oauth2)")
    parser.add_argument("--tools", nargs="*", default=[], help="Tool names exposed by this server")
    parser.add_argument("--capabilities", nargs="*", default=[], help="Capability keywords for runtime matching")
    parser.add_argument("--author", "-a", default="", help="GitHub username of the contributor")
    return parser.parse_args()


def validate_name(name: str) -> None:
    """Exit with an error if the name does not match the required pattern."""
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        print(f"Error: name must match ^[a-z][a-z0-9_]*$ — got '{name}'")
        sys.exit(1)


def validate_auth(args: argparse.Namespace) -> None:
    """Exit with an error if auth-related arguments are inconsistent."""
    if args.auth == "api_key" and not args.auth_env:
        print("Error: --auth-env is required when --auth is api_key")
        sys.exit(1)
    if args.auth == "oauth2" and not args.auth_provider:
        print("Error: --auth-provider is required when --auth is oauth2")
        sys.exit(1)


def build_config(args: argparse.Namespace) -> McpConfig:
    """Construct an McpConfig from parsed CLI arguments."""
    name = args.name.lower().replace("-", "_").replace(" ", "_")
    validate_name(name)

    description = args.description or f"{name.replace('_', ' ').title()} MCP server — {args.package}"
    capabilities = args.capabilities or [name.replace("_", " ")]

    return McpConfig(
        name=name,
        package=args.package,
        description=description,
        category=args.category,
        auth_type=args.auth,
        auth_env=args.auth_env,
        auth_provider=args.auth_provider,
        tools=args.tools,
        capabilities=capabilities,
        author=args.author,
    )


def scaffold_mcp(config: McpConfig) -> None:
    """Create the MCP directory and write all scaffold files."""
    if os.path.exists(config.mcp_dir):
        print(f"Error: mcps/{config.name}/ already exists")
        sys.exit(1)

    os.makedirs(config.mcp_dir)
    print(f"Creating MCP server: {config.name}")

    create_meta(config)
    create_readme(config)

    print(f"""
MCP server scaffolded at: mcps/{config.name}/

Files created:
  meta.json  — Server metadata (edit to refine tools, capabilities, description)
  README.md  — Setup instructions

Next steps:
  1. Edit meta.json — add specific tools and capabilities for better runtime matching
  2. Verify the package works: npx -y {config.package}
  3. Submit a PR using the mcp PR template
""")


def main() -> None:
    """Entry point: parse arguments, validate, and scaffold the MCP server."""
    args = parse_args()
    validate_auth(args)
    config = build_config(args)
    scaffold_mcp(config)


if __name__ == "__main__":
    main()
