# Sentient Community

Community hub for sharing brain adapters, nerve bundles, and connector implementations for [Sentient](https://github.com/otomus/sentient).

## What's Here

| Directory | Contents | Description |
|-----------|----------|-------------|
| `nerves/` | Nerve bundles | Identity + tools + test cases for autonomous agents |
| `adapters/brain/` | Brain adapters | Per-model system prompts, LoRA weights, qualification scores |
| `connectors/` | Connectors | Full implementations for messaging platforms |

## Quick Start

### Install a nerve from the community

```bash
# In your sentient directory
python cli.py nerve install weather_nerve
```

### Export and share your nerve

```bash
# Export a qualified nerve
python cli.py export nerve my_nerve

# Contribute it to the community
python cli.py contribute nerve my_nerve
```

### Browse available nerves

```bash
python cli.py nerve search "weather"
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on submitting nerves, adapters, and connectors.

### Requirements

- **Nerves**: Must include `bundle.json`, `test_cases.json` (>=4 cases), and tool implementations
- **Adapters**: Must include `meta.json`, `context.json`, and `qualification.json` with score 0.0-1.0
- **Connectors**: Must include `meta.json`, `config-template.json` (no secrets), and a README

### Validation

All PRs are automatically validated by CI:
- JSON schema validation
- Secret scanning (API keys, private keys, absolute paths)
- Tool safety checks (no `eval`, `exec`, `os.system`, `subprocess`)
- Structural completeness checks

## Manifest

The `manifest.json` file is auto-generated on merge and contains an index of all contributions. Use it to search and discover community content programmatically.

## License

MIT License — see [LICENSE](LICENSE).
