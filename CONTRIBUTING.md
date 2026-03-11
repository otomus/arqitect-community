# Contributing to Sentient Community

Thank you for contributing! This guide covers how to submit nerves, brain adapters, and connectors.

## General Rules

1. **No secrets** — Never commit API keys, tokens, passwords, or private keys
2. **No absolute paths** — Use relative paths only; no `/Users/`, `/home/`, `C:\Users\`
3. **Safe tools only** — No `os.system`, `eval`, `exec`, `subprocess`, or `__import__` in tool code
4. **Schema compliance** — All JSON files must validate against schemas in `schemas/`

## Submitting a Nerve

### Using the CLI (recommended)

```bash
# In your sentient directory
python cli.py contribute nerve my_nerve
```

This exports, validates, and creates a PR automatically.

### Manual submission

1. Create `nerves/{nerve_name}/bundle.json` following `schemas/bundle.schema.json`
2. Create `nerves/{nerve_name}/test_cases.json` with at least 4 test cases:
   - At least 1 core test (tests primary functionality)
   - At least 1 negative test (tests rejection of out-of-scope input)
3. Add tool implementations in `nerves/{nerve_name}/tools/{tool_name}/`
   - `spec.json` — Language-agnostic interface definition
   - `python/{tool_name}.py` — Python implementation
4. Open a PR using the nerve template

### Test Case Requirements

```json
[
  {"input": "What's the weather in Paris?", "type": "core", "expected_keywords": ["paris", "weather"]},
  {"input": "Tell me a joke", "type": "negative", "expect_reject": true}
]
```

## Submitting a Brain Adapter

1. Create `adapters/brain/{model_name}/meta.json` — model info and capabilities
2. Create `adapters/brain/{model_name}/context.json` — system prompt and config
3. Create `adapters/brain/{model_name}/qualification.json` — scores breakdown
4. Optionally add `adapter.gguf` for LoRA weights (tracked by Git LFS)

## Submitting a Connector

1. Create `connectors/{name}/meta.json` — capabilities and config fields
2. Create `connectors/{name}/config-template.json` — config structure (no real values)
3. Create `connectors/{name}/README.md` — setup instructions
4. Add the implementation (`connector.js` or `connector.py`)

## PR Review Process

1. CI validates schema, scans for secrets, checks safety
2. Maintainers review code quality and completeness
3. Nerves with high qualification scores (>= 0.8) are fast-tracked
