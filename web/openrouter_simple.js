import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import {
    CHOOSE_MODEL,
    NO_MODEL,
    CATALOG_ERROR,
    MEDIA_INPUTS,
    requiredModalities,
    compatibleModels,
    nextModelValue,
} from "./model_filter.mjs";

const NODE_ID = "OpenRouterSimple";

let catalogPromise = null;

async function loadCatalog() {
    if (!catalogPromise) {
        catalogPromise = api.fetchApi("/openrouter_simple/models", { cache: "no-store" })
            .then(async (response) => {
                const payload = await response.json();
                if (!response.ok || !Array.isArray(payload.models)) {
                    throw new Error(payload.warning || `model metadata returned HTTP ${response.status}`);
                }
                return payload;
            })
            .catch((error) => {
                catalogPromise = null;
                throw error;
            });
    }
    return catalogPromise;
}

async function refreshModels(node) {
    const widget = node.widgets?.find((candidate) => candidate.name === "model");
    if (!widget) return;

    try {
        const catalog = await loadCatalog();
        const compatible = compatibleModels(catalog.models, requiredModalities(node.inputs));
        const values = compatible.length ? [CHOOSE_MODEL, ...compatible] : [NO_MODEL];
        widget.options = widget.options || {};
        widget.options.values = values;
        widget.value = compatible.length ? nextModelValue(widget.value, compatible) : NO_MODEL;
        widget.label = catalog.stale
            ? `model (${compatible.length} compatible, cached metadata)`
            : `model (${compatible.length} compatible)`;
        node.openRouterCatalogWarning = catalog.warning || null;
        node.openRouterCatalogRetried = false;
    } catch (error) {
        widget.options = widget.options || {};
        widget.options.values = [CATALOG_ERROR];
        widget.value = CATALOG_ERROR;
        widget.label = "model (catalog unavailable)";
        node.openRouterCatalogWarning = String(error?.message || error);
        if (!node.openRouterCatalogRetried) {
            node.openRouterCatalogRetried = true;
            setTimeout(() => void refreshModels(node), 2000);
        }
    }
    node.graph?.setDirtyCanvas(true, true);
}

function scheduleRefresh(node) {
    queueMicrotask(() => void refreshModels(node));
}

app.registerExtension({
    name: "OpenRouterSimple.ModalityModelFilter",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_ID) return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);
            scheduleRefresh(this);
            return result;
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const result = onConfigure?.apply(this, arguments);
            scheduleRefresh(this);
            return result;
        };

        const onConnectionsChange = nodeType.prototype.onConnectionsChange;
        nodeType.prototype.onConnectionsChange = function (slotType, slotIndex, connected, linkInfo, slot) {
            const result = onConnectionsChange?.apply(this, arguments);
            if (slotType === 1 && MEDIA_INPUTS.has(slot?.name || this.inputs?.[slotIndex]?.name)) {
                scheduleRefresh(this);
            }
            return result;
        };
    },
});
