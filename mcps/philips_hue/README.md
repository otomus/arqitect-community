# philips_hue

Philips Hue smart lighting.

## Installation

This MCP server is installed automatically by arqitect-core. To use it manually:

```bash
npx -y philips-hue-mcp-server
```

## Authentication

Requires an API key. Set the `HUE_BRIDGE_TOKEN` environment variable.

## Tools

- `list_lights` — List all lights
- `set_light` — Set light state (brightness, color, on/off)
- `set_scene` — Activate a scene
- `list_rooms` — List all rooms
- `toggle_light` — Toggle a light on or off

## Capabilities

`lighting` `smart_home` `hue` `automation` `scenes`
