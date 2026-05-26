from comfy_api.latest import ComfyExtension, io

from .core import TYPE_VARS, make_variable, make_variables_from_indexed_strings, merge_vars, render_clip_template, replace_template


PLACEHOLDER_STYLES = ["{name}", "{{name}}", "$(name)", "$name"]
MISSING_MODES = ["keep", "empty", "error"]
TemplateVars = io.Custom(TYPE_VARS)
ClipType = getattr(io, "Clip", getattr(io, "CLIP", io.Custom("CLIP")))
ConditioningType = getattr(io, "Conditioning", io.Custom("CONDITIONING"))


def _sorted_autogrow_values(values):
    if not values:
        return []
    if isinstance(values, dict):
        return [values[key] for key in sorted(values, key=_autogrow_sort_key)]
    return list(values)


def _sorted_autogrow_items(values):
    if not values:
        return []
    if isinstance(values, dict):
        return [
            (_autogrow_index(key), values[key])
            for key in sorted(values, key=_autogrow_sort_key)
        ]
    return list(enumerate(values))


def _autogrow_index(key):
    suffix = key[len(key.rstrip("0123456789")):]
    if suffix:
        return int(suffix)
    return 0


def _autogrow_sort_key(key):
    prefix = key.rstrip("0123456789")
    suffix = key[len(prefix):]
    if suffix:
        return (prefix, int(suffix))
    return (prefix, -1)


class TemplateVariable(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="TemplateVariable",
            display_name="Template Variable",
            category="Template Vars",
            inputs=[
                io.String.Input("name", default="character", multiline=False),
                io.String.Input(
                    "value",
                    default="",
                    multiline=True,
                    dynamic_prompts=False,
                ),
            ],
            outputs=[
                TemplateVars.Output(display_name="variables"),
            ],
        )

    @classmethod
    def execute(cls, name, value):
        return io.NodeOutput(make_variable(name, value))


class TemplateVariableFromString(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="TemplateVariableFromString",
            display_name="Template Variable From String",
            category="Template Vars",
            inputs=[
                io.String.Input("name", default="character", multiline=False),
                io.String.Input("value", optional=True, force_input=True),
            ],
            outputs=[
                TemplateVars.Output(display_name="variables"),
            ],
        )

    @classmethod
    def execute(cls, name, value=""):
        return io.NodeOutput(make_variable(name, value))


class TemplateVariablesFromStrings(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        template = io.Autogrow.TemplatePrefix(
            input=io.String.Input("value", force_input=True),
            prefix="value",
            min=1,
            max=100,
        )
        return io.Schema(
            node_id="TemplateVariablesFromStrings",
            display_name="Template Variables From Strings",
            category="Template Vars",
            inputs=[
                io.String.Input(
                    "names",
                    default="value0",
                    multiline=True,
                    dynamic_prompts=False,
                ),
                io.Autogrow.Input("values", template=template),
            ],
            outputs=[
                TemplateVars.Output(display_name="variables"),
            ],
        )

    @classmethod
    def execute(cls, names, values):
        return io.NodeOutput(make_variables_from_indexed_strings(names, _sorted_autogrow_items(values)))


class MergeTemplateVariables(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        template = io.Autogrow.TemplatePrefix(
            input=TemplateVars.Input("variables"),
            prefix="variables",
            min=1,
            max=100,
        )
        return io.Schema(
            node_id="MergeTemplateVariables",
            display_name="Merge Template Variables",
            category="Template Vars",
            inputs=[
                io.Autogrow.Input("variables", template=template),
            ],
            outputs=[
                TemplateVars.Output(display_name="variables"),
            ],
        )

    @classmethod
    def execute(cls, variables):
        return io.NodeOutput(merge_vars(_sorted_autogrow_values(variables)))


class ApplyTemplateVariables(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="ApplyTemplateVariables",
            display_name="Apply Template Variables",
            category="Template Vars",
            inputs=[
                io.String.Input(
                    "template",
                    default="This is {character1} and {character2} standing in {location}.",
                    multiline=True,
                    dynamic_prompts=False,
                ),
                io.Combo.Input("placeholder_style", options=PLACEHOLDER_STYLES, default="{name}"),
                io.Combo.Input("missing", options=MISSING_MODES, default="keep"),
                TemplateVars.Input("variables", optional=True),
            ],
            outputs=[
                io.String.Output(display_name="text"),
            ],
        )

    @classmethod
    def execute(cls, template, placeholder_style, missing, variables=None):
        return io.NodeOutput(replace_template(template, variables, placeholder_style, missing))


class CLIPTextEncodeWithTemplateVariables(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="CLIPTextEncodeWithTemplateVariables",
            display_name="CLIP Text Encode With Template Variables",
            category="Template Vars",
            inputs=[
                ClipType.Input("clip"),
                io.String.Input(
                    "text",
                    default="",
                    multiline=True,
                    placeholder="text",
                    dynamic_prompts=False,
                ),
                TemplateVars.Input("variables", optional=True),
            ],
            outputs=[
                ConditioningType.Output(display_name="conditioning"),
                io.String.Output(display_name="preview"),
            ],
        )

    @classmethod
    def execute(cls, clip, text, variables=None):
        rendered = render_clip_template(text, variables)
        tokens = clip.tokenize(rendered)
        return io.NodeOutput(clip.encode_from_tokens_scheduled(tokens), rendered)


class TemplateVarsExtension(ComfyExtension):
    async def get_node_list(self):
        return [
            TemplateVariable,
            TemplateVariableFromString,
            TemplateVariablesFromStrings,
            MergeTemplateVariables,
            ApplyTemplateVariables,
            CLIPTextEncodeWithTemplateVariables,
        ]


async def comfy_entrypoint():
    return TemplateVarsExtension()
