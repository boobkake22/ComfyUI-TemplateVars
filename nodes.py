from .core import TYPE_VARS, make_variable, make_variables_from_indexed_strings, merge_vars, render_clip_template, replace_template


class TemplateVariable:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": "character", "multiline": False}),
                "value": (
                    "STRING",
                    {"default": "", "multiline": True, "dynamicPrompts": False},
                ),
            }
        }

    RETURN_TYPES = (TYPE_VARS,)
    RETURN_NAMES = ("variables",)
    FUNCTION = "make"
    CATEGORY = "Template Vars"

    def make(self, name, value):
        return (make_variable(name, value),)


class TemplateVariableFromString:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": "character", "multiline": False}),
            },
            "optional": {
                "value": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = (TYPE_VARS,)
    RETURN_NAMES = ("variables",)
    FUNCTION = "make"
    CATEGORY = "Template Vars"

    def make(self, name, value=""):
        return (make_variable(name, value),)


class TemplateVariablesFromStrings:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            f"value_{index}": ("STRING", {"forceInput": True})
            for index in range(1, 11)
        }
        return {
            "required": {
                "names": (
                    "STRING",
                    {
                        "default": "value0",
                        "multiline": True,
                        "dynamicPrompts": False,
                    },
                ),
            },
            "optional": optional,
        }

    RETURN_TYPES = (TYPE_VARS,)
    RETURN_NAMES = ("variables",)
    FUNCTION = "make"
    CATEGORY = "Template Vars"

    def make(self, names, **kwargs):
        values = [
            (index - 1, kwargs[f"value_{index}"])
            for index in range(1, 11)
            if f"value_{index}" in kwargs
        ]
        return (make_variables_from_indexed_strings(names, values),)


class MergeTemplateVariables:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            f"variables_{index}": (TYPE_VARS, {"forceInput": True})
            for index in range(1, 11)
        }
        return {"optional": optional}

    RETURN_TYPES = (TYPE_VARS,)
    RETURN_NAMES = ("variables",)
    FUNCTION = "merge"
    CATEGORY = "Template Vars"

    def merge(self, **kwargs):
        return (merge_vars(kwargs[key] for key in sorted(kwargs)),)


class ApplyTemplateVariables:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "template": (
                    "STRING",
                    {
                        "default": "This is {character1} and {character2} standing in {location}.",
                        "multiline": True,
                        "dynamicPrompts": False,
                    },
                ),
                "placeholder_style": (["{name}", "{{name}}", "$(name)", "$name"],),
                "missing": (["keep", "empty", "error"],),
            },
            "optional": {
                "variables": (TYPE_VARS, {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "apply"
    CATEGORY = "Template Vars"

    def apply(self, template, placeholder_style, missing, variables=None):
        return (replace_template(template, variables, placeholder_style, missing),)


class CLIPTextEncodeWithTemplateVariables:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "text": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "dynamicPrompts": False,
                        "placeholder": "text",
                    },
                ),
            },
            "optional": {
                "variables": (TYPE_VARS, {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("CONDITIONING", "STRING")
    RETURN_NAMES = ("conditioning", "preview")
    FUNCTION = "encode"
    CATEGORY = "Template Vars"

    def encode(self, clip, text, variables=None):
        rendered = render_clip_template(text, variables)
        tokens = clip.tokenize(rendered)
        return (clip.encode_from_tokens_scheduled(tokens), rendered)


NODE_CLASS_MAPPINGS = {
    "TemplateVariable": TemplateVariable,
    "TemplateVariableFromString": TemplateVariableFromString,
    "TemplateVariablesFromStrings": TemplateVariablesFromStrings,
    "MergeTemplateVariables": MergeTemplateVariables,
    "ApplyTemplateVariables": ApplyTemplateVariables,
    "CLIPTextEncodeWithTemplateVariables": CLIPTextEncodeWithTemplateVariables,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TemplateVariable": "Template Variable",
    "TemplateVariableFromString": "Template Variable From String",
    "TemplateVariablesFromStrings": "Template Variables From Strings",
    "MergeTemplateVariables": "Merge Template Variables",
    "ApplyTemplateVariables": "Apply Template Variables",
    "CLIPTextEncodeWithTemplateVariables": "CLIP Text Encode With Template Variables",
}
