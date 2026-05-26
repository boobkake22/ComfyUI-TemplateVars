import re
from copy import deepcopy


TYPE_VARS = "TEMPLATE_VARS"
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def clean_name(name):
    name = str(name).strip()
    if not name:
        raise ValueError("Variable name cannot be empty.")
    if not NAME_RE.match(name):
        raise ValueError(
            "Variable names must start with a letter or underscore and only "
            "contain letters, numbers, underscores, or hyphens."
        )
    return name


def clean_value(value):
    value = "" if value is None else str(value)
    return value.strip()


def copy_vars(variables):
    if not variables:
        return {}
    if isinstance(variables, dict):
        return deepcopy(variables)
    raise TypeError("Template variables must be a dictionary-like TEMPLATE_VARS value.")


def merge_vars(variable_maps):
    merged = {}
    for variables in variable_maps:
        merged.update(copy_vars(variables))
    return merged


def make_variable(name, value):
    return {clean_name(name): clean_value(value)}


def split_names(names):
    if names is None:
        return []
    return [line.strip() for line in str(names).splitlines()]


def make_variables_from_strings(names, values, default_prefix="value"):
    return make_variables_from_indexed_strings(
        names,
        enumerate(values),
        default_prefix=default_prefix,
    )


def make_variables_from_indexed_strings(names, indexed_values, default_prefix="value"):
    names = split_names(names)
    variables = {}

    for index, value in indexed_values:
        if value is None:
            continue

        name = names[index] if index < len(names) and names[index] else f"{default_prefix}{index}"
        variables[clean_name(name)] = clean_value(value)

    return variables


def pattern_for_style(style):
    if style == "{name}":
        return re.compile(r"\{\s*([A-Za-z_][A-Za-z0-9_-]*)\s*(?:\|\s*([^{}]*?)\s*)?\}")
    if style == "{{name}}":
        return re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_-]*)\s*(?:\|\s*([^{}]*?)\s*)?\}\}")
    if style == "$(name)":
        return re.compile(r"\$\(\s*([A-Za-z_][A-Za-z0-9_-]*)\s*(?::\s*([^)]*?)\s*)?\)")
    if style == "$name":
        return re.compile(r"\$([A-Za-z_][A-Za-z0-9_-]*)")
    raise ValueError(f"Unknown placeholder style: {style}")


def replace_template(template, variables, style, missing):
    variables = variables or {}
    pattern = pattern_for_style(style)

    def replacement(match):
        name = match.group(1).strip()
        default = match.group(2) if len(match.groups()) > 1 else None

        if name in variables:
            return str(variables[name])
        if default is not None:
            return default
        if missing == "keep":
            return match.group(0)
        if missing == "empty":
            return ""
        raise KeyError(f"Missing template variable: {name}")

    return pattern.sub(replacement, template or "")


def clip_template_variables(template):
    template = template or ""
    variables = []
    index = 0

    while index < len(template):
        char = template[index]

        if char == "}":
            raise ValueError(f"Unmatched closing brace at character {index}.")

        if char != "{":
            index += 1
            continue

        close_index = template.find("}", index + 1)
        if close_index == -1:
            raise ValueError(f"Unmatched opening brace at character {index}.")

        placeholder = template[index + 1:close_index].strip()
        if "{" in placeholder:
            raise ValueError(f"Nested opening brace inside placeholder at character {index}.")
        if not placeholder:
            raise ValueError(f"Empty template variable placeholder at character {index}.")
        if not NAME_RE.match(placeholder):
            raise ValueError(
                f"Invalid template variable '{placeholder}'. Variable names must start "
                "with a letter or underscore and only contain letters, numbers, "
                "underscores, or hyphens."
            )

        variables.append(placeholder)
        index = close_index + 1

    return variables


def render_clip_template(template, variables):
    variables = copy_vars(variables)
    used_variables = clip_template_variables(template)
    missing_variables = sorted(set(used_variables) - set(variables))

    if missing_variables:
        missing = ", ".join(missing_variables)
        raise ValueError(f"Missing template variable(s): {missing}")

    return replace_template(template, variables, "{name}", "error")
