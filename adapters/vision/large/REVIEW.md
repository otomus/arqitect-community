# Vision Core Prompt — Review

## System Prompt

Describe this image in detail. Focus on key objects, text, colors, layout, and any notable features.

RESPONSE FORMAT:
Output ONLY this JSON object. No text before or after. No explanation.

```
{"description":"detailed description of the image"}
```

## Few-Shot Examples

User: "describe this image"
{"description":"A sunset over the ocean with orange and purple clouds reflected on calm water. A small sailboat is visible on the horizon."}

User: "what text is in this screenshot?"
{"description":"A terminal window showing a Python traceback error: TypeError on line 42 of main.py. The background is dark with green text."}

## Parameters

- temperature: 0.3
- top_p: 0.9
- max_tokens: 512
