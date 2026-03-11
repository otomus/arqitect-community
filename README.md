# Sentient Community

Community hub for sharing brain adapters, nerve bundles, and connector implementations for [Sentient](https://github.com/otomus/sentient).

## What's Here

| Directory | Contents | Description |
|-----------|----------|-------------|
| `nerves/` | Nerve bundles | Identity + tools + test cases for autonomous agents |
| `adapters/brain/` | Brain adapters | Per-model system prompts, LoRA weights, qualification scores |
| `connectors/` | Connectors | Full implementations for messaging platforms |

## How It Works

Nerves are **not manually installed**. When Sentient's brain synthesizes a nerve, it automatically checks this community repo for a matching bundle. If one exists, the proven identity (system prompt, examples, tools, test cases) is used instead of generating from scratch.

### Sync community content

```bash
# Pull the latest manifest and bundles to your local cache
python cli.py community sync
```

After syncing, the synthesis pipeline will automatically use community bundles when creating nerves that match.

### Search available nerves

```bash
python cli.py community search "weather"
```

### Contribute a nerve

```bash
# Export a qualified nerve and open a PR
python cli.py contribute nerve my_nerve
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
