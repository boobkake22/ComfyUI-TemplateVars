import { app } from "../../scripts/app.js";


const TRIM_NODE_TYPES = new Set([
  "TemplateVariable",
  "TemplateVariableFromString",
]);
const STRING_LIST_NODE_TYPE = "TemplateVariablesFromStrings";
const GENERATED_NAME_PREFIX = "name";


function trimString(value) {
  return String(value ?? "").trim();
}


function namesWidget(node) {
  return node.widgets?.find((widget) => widget.name === "names");
}


function generatedNameWidgetName(index) {
  return `${GENERATED_NAME_PREFIX}${index}`;
}


function generatedNameWidgets(node) {
  return (node.widgets ?? []).filter((widget) => widget.__templateVarsNameWidget);
}


function parseValueInput(input) {
  const name = input?.name ?? "";

  let match = /^values\.value(\d+)$/.exec(name);
  if (match) {
    return {
      index: Number(match[1]),
      input,
    };
  }

  match = /^value(\d+)$/.exec(name);
  if (match) {
    return {
      index: Number(match[1]),
      input,
    };
  }

  match = /^value_(\d+)$/.exec(name);
  if (match) {
    return {
      index: Number(match[1]) - 1,
      input,
    };
  }

  return null;
}


function valueInputs(node) {
  return (node.inputs ?? [])
    .map(parseValueInput)
    .filter(Boolean)
    .sort((a, b) => a.index - b.index);
}


function connectedValueInputs(node) {
  return valueInputs(node).filter(({ input }) => input.link != null);
}


function readNameLines(node) {
  return String(namesWidget(node)?.value ?? "")
    .split(/\r?\n/)
    .map((line) => line.trim());
}


function nameForIndex(node, index) {
  const lines = readNameLines(node);
  return lines[index] || `value${index}`;
}


function syncNamesFromWidgets(node) {
  const widget = namesWidget(node);
  if (!widget) return;

  const lines = readNameLines(node);
  for (const nameWidget of generatedNameWidgets(node)) {
    const index = nameWidget.__templateVarsIndex;
    if (!Number.isInteger(index)) continue;

    while (lines.length <= index) {
      lines.push("");
    }

    lines[index] = trimString(nameWidget.value) || `value${index}`;
    nameWidget.value = lines[index];
  }

  while (lines.length && lines[lines.length - 1] === "") {
    lines.pop();
  }

  widget.value = lines.join("\n");
}


function removeGeneratedNameWidgets(node, activeIndexes) {
  if (!node.widgets) return;

  for (let index = node.widgets.length - 1; index >= 0; index--) {
    const widget = node.widgets[index];
    if (!widget.__templateVarsNameWidget) continue;
    if (activeIndexes.has(widget.__templateVarsIndex)) continue;

    widget.onRemove?.();
    node.widgets.splice(index, 1);
  }
}


function createNameWidget(node, index) {
  const widgetName = generatedNameWidgetName(index);
  const existing = generatedNameWidgets(node).find((widget) => widget.__templateVarsIndex === index);
  if (existing) return existing;

  const result = app.widgets.STRING?.(
    node,
    widgetName,
    ["STRING", { default: nameForIndex(node, index), multiline: false }],
    app
  );
  const widget = result?.widget ?? node.widgets?.[node.widgets.length - 1];
  if (!widget) return null;

  widget.name = widgetName;
  widget.label = `value${index} name`;
  widget.serialize = false;
  widget.__templateVarsNameWidget = true;
  widget.__templateVarsIndex = index;

  const original = widget.callback;
  widget.callback = function (...args) {
    if (typeof args[0] === "string") {
      args[0] = args[0].trim();
    }

    const result = original?.apply(this, args);
    widget.value = trimString(widget.value) || `value${index}`;
    syncNamesFromWidgets(node);
    return result;
  };

  return widget;
}


function orderGeneratedNameWidgets(node) {
  if (!node.widgets) return;

  const generated = generatedNameWidgets(node).sort(
    (a, b) => a.__templateVarsIndex - b.__templateVarsIndex
  );
  if (!generated.length) return;

  node.widgets = node.widgets.filter((widget) => !widget.__templateVarsNameWidget);

  const hiddenIndex = node.widgets.findIndex((widget) => widget.name === "names");
  const insertionIndex = hiddenIndex === -1 ? node.widgets.length : hiddenIndex + 1;
  node.widgets.splice(insertionIndex, 0, ...generated);
}


function refreshStringListUi(node) {
  if (node.comfyClass !== STRING_LIST_NODE_TYPE) return;

  const widget = namesWidget(node);
  if (widget) {
    widget.hidden = true;
    widget.serialize = true;
  }

  const active = connectedValueInputs(node);
  const activeIndexes = new Set(active.map(({ index }) => index));

  removeGeneratedNameWidgets(node, activeIndexes);
  for (const { index } of active) {
    const nameWidget = createNameWidget(node, index);
    if (nameWidget) {
      nameWidget.value = trimString(nameWidget.value) || nameForIndex(node, index);
    }
  }

  orderGeneratedNameWidgets(node);
  syncNamesFromWidgets(node);

  node.size = node.computeSize?.([...node.size]) ?? node.size;
  node.setDirtyCanvas?.(true, true);
}


function installStringListUi(node) {
  if (node.comfyClass !== STRING_LIST_NODE_TYPE || node.__templateVarsStringListInstalled) return;
  node.__templateVarsStringListInstalled = true;

  const originalConnectionsChange = node.onConnectionsChange;
  node.onConnectionsChange = function (...args) {
    const result = originalConnectionsChange?.apply(this, args);
    requestAnimationFrame(() => refreshStringListUi(this));
    return result;
  };

  const originalSerialize = node.serialize;
  if (originalSerialize) {
    node.serialize = function (...args) {
      syncNamesFromWidgets(this);
      return originalSerialize.apply(this, args);
    };
  }

  requestAnimationFrame(() => refreshStringListUi(node));
}


function trimWidget(widget) {
  if (!widget || typeof widget.value !== "string") return;

  const trimmed = widget.value.trim();
  if (trimmed === widget.value) return;

  widget.value = trimmed;
}


function wrapTrimCallback(widget) {
  if (!widget || widget.__templateVarsTrimWrapped) return;
  widget.__templateVarsTrimWrapped = true;

  const original = widget.callback;
  widget.callback = function (...args) {
    trimWidget(widget);
    if (typeof args[0] === "string") {
      args[0] = args[0].trim();
    }
    return original?.apply(this, args);
  };
}


function installBasicTrimming(node) {
  if (!TRIM_NODE_TYPES.has(node.comfyClass)) return;

  for (const widget of node.widgets ?? []) {
    if (widget.name !== "name" && widget.name !== "value") continue;

    trimWidget(widget);
    wrapTrimCallback(widget);
  }
}


app.registerExtension({
  name: "template_vars.ui",

  nodeCreated(node) {
    installBasicTrimming(node);
    installStringListUi(node);
  },

  loadedGraphNode(node) {
    installBasicTrimming(node);
    installStringListUi(node);
  },
});
