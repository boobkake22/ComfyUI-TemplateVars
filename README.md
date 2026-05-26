# ComfyUI Template Vars

Small ComfyUI nodes for scoped, graph-based string variables.

This node pack is intentionally narrow:

- no global variable dictionary
- no file storage
- no JSON editing required
- no positional `arg0`, `arg1`, `arg2` inputs

Variables are normal node outputs. You create named variable maps, merge them, then apply them to a template string.
Template text widgets explicitly disable ComfyUI dynamic prompt expansion so `{name}` placeholders are treated as template variables.

On current ComfyUI builds, this pack uses the V3 node API and the merge node uses Autogrow inputs, like the modern Batch Images node. Older ComfyUI builds fall back to a V1 implementation with fixed merge inputs.

## Nodes

### Template Variable

Creates one variable from widget text.

Inputs:

- `name`: variable name, such as `character1`
- `value`: replacement text

Variable names and values are automatically stripped of leading/trailing whitespace. Variable names must start with a letter or underscore and can contain letters, numbers, underscores, or hyphens.

Outputs:

- `variables`: a `TEMPLATE_VARS` value

### Template Variable From String

Creates one variable from a connected string input.

Use this when another node already produced the value and you only want to attach a variable name to it.

Inputs:

- `name`: variable name
- `value`: connected string input

Connected string values are automatically stripped of leading/trailing whitespace.

### Template Variables From Strings

Creates and merges multiple variables from connected string inputs.

On current ComfyUI builds, this node uses Autogrow value inputs. It starts with one `value` hookup and grows as you connect more strings, up to 100 values. On older fallback builds, it exposes 10 fixed value inputs.

When the frontend helper loads, the backend `names` field is hidden and replaced by one single-line name widget for each connected `valueN` input. Those generated name widgets are synced back into `names`, so the workflow remains compatible with ComfyUI instances that do not load the helper.

Inputs:

- `names`: one variable name per line, used as the backend/fallback field
- `value0`, `value1`, etc.: connected string values on current ComfyUI
- `value_1`, `value_2`, etc.: connected string values on older fallback builds

Example:

```text
names:
character1
character2
location
```

Connected values:

```text
value0 = Alice
value1 = Bob
value2 = a rainy train station
```

Output:

```text
{
  "character1": "Alice",
  "character2": "Bob",
  "location": "a rainy train station"
}
```

The output is already a `TEMPLATE_VARS` map, so it can connect directly to **CLIP Text Encode With Template Variables**.

If a name line is blank or missing, the node falls back to `value0`, `value1`, etc. for that value index.

### Merge Template Variables

Merges `TEMPLATE_VARS` inputs into one variable map.

Later inputs override earlier inputs with the same name.

On current ComfyUI builds, this node starts with one variable input and dynamically grows as you connect more inputs. It supports up to 100 variable maps. On older fallback builds, it exposes 10 fixed inputs.

### Apply Template Variables

Applies a variable map to a template and outputs a string.

Example template:

```text
This is {character1} and {character2} standing in {location}.
```

Supported placeholder styles:

- `{name}`
- `{{name}}`
- `$(name)`
- `$name`

Missing variable behavior:

- `keep`: leave the placeholder unchanged
- `empty`: replace missing placeholders with an empty string
- `error`: stop with an error

Defaults are supported for the bracketed styles:

```text
This is {character1|someone} standing in {location|an empty room}.
This is {{character1|someone}} standing in {{location|an empty room}}.
This is $(character1:someone) standing in $(location:an empty room).
```

### CLIP Text Encode With Template Variables

Convenience node that applies variables, then encodes the rendered prompt with CLIP.

This node intentionally keeps the UI small:

- prompt field is blank by default and uses `text` as its placeholder
- placeholder style is fixed to `{name}`
- unmatched braces raise an error
- missing variables raise an error
- output 1 is `conditioning`; output 2 is `preview`, the rendered prompt text

You can also use `Apply Template Variables` and send its string output to another conditioning/prompt node.

## Example Workflow Shape

```text
String node -> Template Variable From String, name=character1
String node -> Template Variable From String, name=character2
String node -> Template Variable From String, name=location

variable outputs -> Merge Template Variables

template:
This is {character1} and {character2} standing in {location}.

merged variables + template -> Apply Template Variables -> prompt conditioner
```

## Installation

Copy this folder into:

```text
ComfyUI/custom_nodes/ComfyUI-TemplateVars
```

Then restart ComfyUI.

The nodes appear under:

```text
Template Vars
```
