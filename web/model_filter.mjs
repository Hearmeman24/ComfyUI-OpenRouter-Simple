export const CHOOSE_MODEL = "— choose a compatible OpenRouter model —";
export const NO_MODEL = "— no compatible text-output model —";
export const CATALOG_ERROR = "— OpenRouter model catalog unavailable —";
export const MEDIA_INPUTS = new Set(["image", "video", "audio"]);

export function requiredModalities(inputs = []) {
    const required = new Set(["text"]);
    for (const input of inputs) {
        if (MEDIA_INPUTS.has(input?.name) && input.link != null) {
            required.add(input.name);
        }
    }
    return required;
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
