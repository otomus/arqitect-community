## Brain Adapter Contribution

**Model**: <!-- e.g., qwen2.5-7b -->
**Size class**: <!-- tiny | small | medium | large -->
**Provider**: <!-- gguf | ollama | anthropic | groq | openai_compat -->

### Capabilities
- JSON mode: <!-- yes/no -->
- Tool calling: <!-- yes/no -->
- Max context: <!-- e.g., 8192 -->

### Qualification
- **Score**: <!-- e.g., 0.82 -->
- **Has LoRA weights**: <!-- yes/no -->

### Checklist
- [ ] `meta.json` validates against schema
- [ ] `context.json` validates against schema
- [ ] `qualification.json` has valid score (0.0-1.0)
- [ ] No secrets or absolute paths
- [ ] LoRA file (if any) is tracked by Git LFS
