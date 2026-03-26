# Arqitect Community — Claude Instructions

## PR Reviews

When reviewing any PR in this repository, **always read `CONTRIBUTING.md` first** before evaluating any diff. Use it as the authoritative checklist for what is and isn't acceptable.

### Auto-close without review (no feedback needed)
- **Regressions**: any PR where a `qualification_score` in any tier is lower than the current value on `main` → close immediately
- **Duplicates**: any PR for a nerve/adapter/tool that already has an open PR → close the newer one immediately

For auto-closes, post a brief comment explaining the reason (regression or duplicate) and close the PR.

### Review process
1. Read `CONTRIBUTING.md`
2. Fetch the PR diff (`gh pr diff <number>`) and PR details (`gh pr view <number>`)
3. Check against every applicable section in `CONTRIBUTING.md` for the contribution type (nerve, adapter, tool, connector, MCP)
4. Post findings as a comment on the PR
