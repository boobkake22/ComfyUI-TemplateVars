try:
    from comfy_api.latest import io as _io

    if not hasattr(_io, "Autogrow"):
        raise ImportError("ComfyUI V3 Autogrow inputs are not available.")

    from .nodes_v3 import comfy_entrypoint
except ImportError:
    from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

    WEB_DIRECTORY = "./js"

    __all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
else:
    WEB_DIRECTORY = "./js"

    __all__ = ["comfy_entrypoint", "WEB_DIRECTORY"]
