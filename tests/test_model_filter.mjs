import assert from "node:assert/strict";
import test from "node:test";

import {
    CATALOG_ERROR,
    CHOOSE_MODEL,
    compatibleModels,
    nextModelValue,
    requiredModalities,
} from "../web/model_filter.mjs";

const models = [
    { id: "text", input_modalities: ["text"], output_modalities: ["text"] },
    { id: "vision", input_modalities: ["text", "image"], output_modalities: ["text"] },
    { id: "video", input_modalities: ["text", "image", "video"], output_modalities: ["text"] },
    { id: "omni", input_modalities: ["text", "image", "video", "audio"], output_modalities: ["text"] },
    { id: "generator", input_modalities: ["text", "image", "video", "audio"], output_modalities: ["image"] },
];

test("connected modalities are intersected", () => {
    const required = requiredModalities([
        { name: "image", link: 2 },
        { name: "video", link: 3 },
        { name: "audio", link: null },
    ]);
    assert.deepEqual([...required].sort(), ["image", "text", "video"]);
    assert.deepEqual(compatibleModels(models, required), ["omni", "video"]);
});

test("all three media inputs require an omni input model", () => {
    const required = new Set(["text", "image", "video", "audio"]);
    assert.deepEqual(compatibleModels(models, required), ["omni"]);
});

test("an invalid paid model is never silently replaced", () => {
    assert.equal(nextModelValue("vision", ["omni"]), CHOOSE_MODEL);
    assert.equal(nextModelValue("omni", ["omni"]), "omni");
});

test("catalog errors are distinct from an empty compatibility result", () => {
    assert.notEqual(CATALOG_ERROR, "— no compatible text-output model —");
});
