# diagram_create

Create diagram images from text definitions. Supports flowchart, sequence, and class diagrams. Outputs SVG natively; PNG requires cairosvg.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| diagram_type | string | yes | flowchart, sequence, or class |
| definition | string | yes | Text definition of the diagram |
| output_path | string | yes | Output file path (.svg or .png) |

## Syntax

- **Flowchart:** `A -> B -> C -> D`
- **Sequence:** `Client -> Server: request` (one per line)
- **Class:** `ClassName: method1, method2` (one per line)

## Usage

```python
result = run(
    diagram_type="flowchart",
    definition="Start -> Validate -> Process -> End",
    output_path="flow.svg"
)
```
