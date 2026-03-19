# Plan: Nerve Execution Modes — `tool_required` vs `reasoning`

## Problem

Nerves that depend on external tools (weather, stocks, web search) hallucinate answers when their tools aren't available. A 7B model asked "what's the weather in TLV" returns "Sunny with a high of 28°C" from its own knowledge instead of calling a weather API. The system has no way to **enforce** tool usage — it's a soft suggestion in the adapter prompt that small models routinely ignore.

### Root cause

There is no schema-level distinction between:
- **Nerves that MUST call a tool** — weather, crypto_price, news, web_search, calendar (real-time / external data)
- **Nerves that CAN answer from LLM knowledge** — explain, translate, regex, encode (pure reasoning / transformation)

Both types use the same adapter prompt, same template, same qualification flow.

---

## Proposed Change: `mode` field in bundle.json

Add a `mode` field to the nerve bundle schema with two values:

| Mode | Meaning | `action: "answer"` allowed? |
|------|---------|----------------------------|
| `tool_required` | Nerve MUST call an external tool. Hallucinated answers are forbidden. | No — server will redirect to `acquire` |
| `reasoning` | Nerve CAN answer from LLM knowledge. Tools are optional helpers. | Yes |

> **Why `tool_required` and not `tool`?** The `role` field already uses `"tool"` as a value. Using `"tool_required"` avoids semantic collision — `role` describes *what kind of work* the nerve does, `mode` describes *how it must produce answers*.

### Default behavior
- If `mode` is omitted: infer from `tools` field.
  - Non-empty `tools` array → `tool_required`
  - Empty or missing `tools` → `reasoning`
- This keeps backward compatibility — existing bundles get correct behavior without updates.

### Why only two modes?
For tinylm clarity. A third mode like `hybrid` ("try tool, fall back to reasoning") would reintroduce the exact ambiguity this plan eliminates. Small models cannot reliably judge when a tool failure justifies a knowledge-based fallback. Binary is better: you must use a tool, or you can answer.

---

## Changes Required

### 1. Bundle schema (`schemas/bundle.schema.json`)

Add `"mode"` as an optional enum field:

```json
"mode": {
  "type": "string",
  "enum": ["tool_required", "reasoning"],
  "description": "Whether the nerve must call a tool (tool_required) or can answer from LLM knowledge (reasoning). Inferred from tools array if omitted."
}
```

### 2. Bundle files (`nerves/*/bundle.json`)

Add `"mode"` field to each bundle:

```json
{
  "name": "weather_nerve",
  "description": "Get current weather and forecasts",
  "role": "tool",
  "mode": "tool_required",
  "tools": [
    {"name": "weather", "implementations": {}}
  ]
}
```

```json
{
  "name": "explain_nerve",
  "description": "Explain concepts clearly",
  "role": "creative",
  "mode": "reasoning",
  "tools": [
    {"name": "web_search", "implementations": {}}
  ]
}
```

Note: `explain_nerve` has tools but mode is `reasoning` — tools are optional helpers, not required for a valid answer. The mode overrides inference from the tools array.

### 3. Manifest schema (`schemas/manifest.schema.json`)

Add `mode` to the per-nerve entry schema so the manifest can carry it.

### 4. Manifest generator (`scripts/generate_manifest.py`)

Update `collect_nerves()` to read `mode` from each bundle.json and include it in the manifest output. If `mode` is missing from a bundle, apply the default inference rule (non-empty tools → `tool_required`, else `reasoning`).

### 5. Manifest (`manifest.json`)

Auto-generated — will include `mode` after step 4 is done:

```json
{
  "weather_nerve": {
    "description": "Get current weather and forecasts",
    "role": "tool",
    "mode": "tool_required",
    "tools": ["weather"]
  }
}
```

### 6. Adapter prompts (`adapters/nerve/*/context.json`)

No changes needed. The `mode` field is consumed by the **server-side nerve template**, not the adapter. The current nerve adapter prompt already says "NEVER answer from your own knowledge when a tool can provide data" — this rule stays, but the server now **enforces** it for `mode: "tool_required"` nerves at the code level rather than relying on the LLM to obey.

### 7. Tag existing nerves

Every existing bundle.json needs a `mode` field. Classification:

**`"mode": "tool_required"` — must call a tool, answer is never acceptable:**

| Nerve | Reason |
|-------|--------|
| weather_nerve | Real-time data |
| news_nerve | Real-time data |
| crypto_price_nerve | Real-time data |
| web_search_nerve | External data |
| web_scrape_nerve | External data |
| web_fetch_nerve | External data |
| calendar_nerve | External service |
| email_nerve | External service |
| sms_send_nerve | External service |
| notification_nerve | External service |
| dns_check_nerve | External data |
| cert_check_nerve | External data |
| port_scan_nerve | External data |
| vuln_scan_nerve | External data |
| youtube_info_nerve | External data |
| youtube_search_nerve | External data |
| youtube_transcript_nerve | External data |
| rss_monitor_nerve | External data |
| sleep_data_nerve | External data |
| music_identify_nerve | External data |
| image_generate_nerve | External service |
| audio_transcribe_nerve | External service (voice MCP) |
| audio_synthesize_nerve | External service (voice MCP) |
| video_transcribe_nerve | External service |
| camera_snapshot_nerve | Hardware |
| device_nerve | Hardware |
| actuator_nerve | Hardware |
| lock_nerve | Hardware |
| db_nerve | External service |
| deploy_nerve | External service |
| docker_nerve | External service |
| ci_check_nerve | External service |
| deep_research_nerve | External data |
| browse_nerve | External web data |
| git_clone_nerve | Remote repository access |
| git_pull_nerve | Remote repository access |
| git_push_nerve | Remote repository access |

**`"mode": "reasoning"` — can answer from LLM knowledge, tools are optional:**

| Nerve | Reason |
|-------|--------|
| translate_nerve | Pure text transformation |
| regex_nerve | Pure computation |
| encode_nerve | Pure computation |
| explain_nerve | LLM knowledge |
| draft_email_nerve | Creative writing |
| draft_blog_nerve | Creative writing |
| copywrite_nerve | Creative writing |
| faq_answer_nerve | LLM knowledge |
| fact_check_nerve | LLM knowledge (tools improve accuracy) |
| code_review_nerve | LLM reasoning |
| json_extract_nerve | Pure transformation |
| csv_nerve | Pure transformation |
| data_clean_nerve | Pure transformation |
| contract_review_nerve | LLM reasoning |
| campaign_plan_nerve | LLM reasoning |
| ad_create_nerve | Creative writing |
| budget_nerve | Computation (tools optional) |
| expense_track_nerve | Computation (tools optional) |
| file_backup_nerve | Local file ops via senses |
| file_diff_nerve | Local file ops via senses |
| file_find_nerve | Local file ops via senses |
| file_organize_nerve | Local file ops via senses |
| file_watch_nerve | Local file ops via senses |
| git_branch_nerve | Local git repo via senses |
| git_cleanup_nerve | Local git repo via senses |
| git_commit_nerve | Local git repo via senses |
| git_conflict_nerve | Local git repo via senses |
| git_history_nerve | Local git repo via senses |
| git_merge_nerve | Local git repo via senses |
| git_rebase_nerve | Local git repo via senses |
| git_stash_nerve | Local git repo via senses |
| git_tag_nerve | Local git repo via senses |
| click_nerve | UI automation via senses |
| scroll_nerve | UI automation via senses |
| type_nerve | UI automation via senses |
| image_ocr_nerve | Local vision sense |
| screen_read_nerve | Local vision sense |
| audio_convert_nerve | Local audio processing |
| audio_record_nerve | Local hardware (mic sense) |

**Rule of thumb**: If the nerve's answer requires data that the LLM cannot possibly know (real-time, user-specific, external system), it's `tool_required`. If the LLM can produce a correct answer from its training data alone, or the nerve operates via local senses, it's `reasoning`.

---

## What the server will do with `mode`

Once the community ships this field, arqitect-server will:

1. **Read `mode` from bundle/manifest** during bootstrap and store in cold memory as nerve metadata
2. **Enforce at runtime** in the nerve template:
   - `mode: "tool_required"` + `action: "answer"` → redirect to `action: "acquire"` (never hallucinate)
   - `mode: "tool_required"` + no tools available → auto-acquire before planning
   - `mode: "reasoning"` + `action: "answer"` → allow (LLM knowledge is valid)
3. **Pre-acquire during qualification**: For `mode: "tool_required"` nerves, acquire tools BEFORE running tests so qualification exercises the full nerve→tool pipeline
4. **Qualification scoring**: `mode: "tool_required"` nerves that answer without calling a tool get score 0 (automatic fail) regardless of how plausible the answer sounds

---

## Migration path

1. Add `"mode"` to `schemas/bundle.schema.json` as optional enum
2. Add `"mode"` to `schemas/manifest.schema.json`
3. Update `scripts/generate_manifest.py` to propagate `mode` to manifest
4. Tag all existing `nerves/*/bundle.json` with explicit `mode`
5. Regenerate `manifest.json`
6. Server reads `mode` — falls back to inferring from `tools` if missing
7. No breaking changes — bundles without `mode` work as before
