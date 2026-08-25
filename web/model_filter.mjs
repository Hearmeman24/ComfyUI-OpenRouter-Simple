export const CHOOSE_MODEL = "— choose a compatible OpenRouter model —";
export const NO_MODEL = "— no compatible text-output model —";
export const CATALOG_ERROR = "— OpenRouter model catalog unavailable —";
export const MEDIA_SPECS = [
    { modality: "image", type: "IMAGE", names: ["image", "image_2", "image_3"] },
    { modality: "video", type: "VIDEO", names: ["video", "video_2", "video_3"] },
    { modality: "audio", type: "AUDIO", names: ["audio", "audio_2", "audio_3"] },
];
export const MEDIA_INPUTS = new Set(MEDIA_SPECS.flatMap((spec) => spec.names));
const LEGACY_WIDGET_COUNT_WITH_SEED = 10;
const LEGACY_SEED_WIDGET_INDEX = 2;

export function migrateLegacySeedWidgetValues(serializedNode) {
    const values = serializedNode?.widgets_values;
    if (Array.isArray(values) && values.length === LEGACY_WIDGET_COUNT_WITH_SEED) {
        values.splice(LEGACY_SEED_WIDGET_INDEX, 1);
    }
}

export function mediaModality(name) {
    return MEDIA_SPECS.find((spec) => spec.names.includes(name))?.modality ?? null;
}

export function requiredModalities(inputs = []) {
    const required = new Set(["text"]);
    for (const input of inputs) {
        const modality = mediaModality(input?.name);
        if (modality && input.link != null) {
            required.add(modality);
        }
    }
    return required;
}

export function desiredMediaInputNames(inputs = []) {
    const linksByName = new Map(inputs.map((input) => [input?.name, input?.link]));
    const desired = new Set();
    for (const spec of MEDIA_SPECS) {
        let highestConnected = -1;
        spec.names.forEach((name, index) => {
            if (linksByName.get(name) != null) highestConnected = index;
        });
        const visibleCount = Math.min(spec.names.length, Math.max(1, highestConnected + 2));
        spec.names.slice(0, visibleCount).forEach((name) => desired.add(name));
    }
    return desired;
}

export function compatibleModels(models, required) {
    return models
        .filter((model) => {
            const inputs = new Set(model.input_modalities || []);
            const outputs = new Set(model.output_modalities || []);
            return outputs.has("text") && [...required].every((item) => inputs.has(item));
        })
        .map((model) => model.id)
        .sort((left, right) => left.localeCompare(right));
}

export function nextModelValue(current, compatible) {
    return compatible.includes(current) ? current : CHOOSE_MODEL;
}
