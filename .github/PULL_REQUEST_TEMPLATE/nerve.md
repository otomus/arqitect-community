## Nerve Contribution

**Nerve name**: <!-- e.g., weather_nerve -->
**Role**: <!-- tool | creative | code -->
**Description**: <!-- What does this nerve do? -->

### Tools included
<!-- List tools this nerve uses -->
-

### Qualification
- **Score**: <!-- e.g., 0.85 -->
- **Test cases**: <!-- e.g., 6 (4 core, 2 negative) -->
- **Model tested on**: <!-- e.g., qwen2.5-coder:32b -->

### Checklist
- [ ] `bundle.json` validates against schema
- [ ] `test_cases.json` has >= 4 cases (>= 1 core, >= 1 negative)
- [ ] All tools have `spec.json` + implementation
- [ ] No secrets or absolute paths in any file
- [ ] Tool code has no `eval`, `exec`, `os.system`, or `subprocess`
