import assert from "node:assert/strict";
import test from "node:test";

import {
    CATALOG_ERROR,
    CHOOSE_MODEL,
    compatibleModels,
    desiredMediaInputNames,
    migrateLegacyWidgetValues,
    nextModelValue,
    requiredModalities,
} from "../web/model_filter.mjs";

test("seed-era saved nodes remove seed and default regenerate on", () => {
    const seedEra = {
        widgets_values: [
            "google/model",
            "auto",
            471994551739533,
            120,
            1.0,
            4096,
            "text",
            false,
            "system",
            "user",
        ],
    };
    migrateLegacyWidgetValues(seedEra);
    assert.deepEqual(seedEra.widgets_values, [
        "google/model",
        "auto",
        120,
        1.0,
        4096,
        "text",
        false,
        true,
        "system",
        "user",
    ]);
});

test("seedless saved nodes gain regenerate without shifting prompts", () => {
    const seedless = {
        widgets_values: [
            "google/model", "auto", 120, 1.0, 4096, "text", false, "system", "user",
        ],
    };
    migrateLegacyWidgetValues(seedless);
    assert.deepEqual(seedless.widgets_values, [
        "google/model", "auto", 120, 1.0, 4096, "text", false, true, "system", "user",
    ]);
});

test("current saved nodes retain an explicit regenerate value", () => {
    const current = {
        widgets_values: [
            "google/model", "auto", 120, 1.0, 4096, "text", false, false, "system", "user",
        ],
    };
    migrateLegacyWidgetValues(current);
    assert.deepEqual(current.widgets_values, [
        "google/model", "auto", 120, 1.0, 4096, "text", false, false, "system", "user",
    ]);
});

const models = [
    { id: "text", input_modalities: ["text"], output_modalities: ["text"] },
    { id: "vision", input_modalities: ["text", "image"], output_modalities: ["text"] },
    { id: "video", input_modalities: ["text", "image", "video"], output_modalities: ["text"] },
    { id: "omni", input_modalities: ["text", "image", "video", "audio"], output_modalities: ["text"] },
    { id: "generator", input_modalities: ["text", "image", "video", "audio"], output_modalities: ["image"] },
];

test("connected modalities are intersected", () => {
    const required = requiredModalities([
        { name: "image_2", link: 2 },
        { name: "video", link: 3 },
        { name: "audio_3", link: null },
    ]);
    assert.deepEqual([...required].sort(), ["image", "text", "video"]);
    assert.deepEqual(compatibleModels(models, required), ["omni", "video"]);
});

test("progressive sockets retain one empty successor per modality", () => {
    const initial = desiredMediaInputNames([
        { name: "image", link: null },
        { name: "image_2", link: null },
        { name: "image_3", link: null },
        { name: "video", link: null },
        { name: "video_2", link: null },
        { name: "video_3", link: null },
        { name: "audio", link: null },
        { name: "audio_2", link: null },
        { name: "audio_3", link: null },
    ]);
    assert.deepEqual([...initial], ["image", "video", "audio"]);

    const growing = desiredMediaInputNames([
        { name: "image", link: 1 },
        { name: "image_2", link: 2 },
        { name: "video", link: 3 },
        { name: "audio", link: null },
    ]);
    assert.deepEqual(
        [...growing],
        ["image", "image_2", "image_3", "video", "video_2", "audio"],
    );
});

test("a restored non-contiguous link never loses its socket", () => {
    const desired = desiredMediaInputNames([
        { name: "image", link: null },
        { name: "image_2", link: 9 },
        { name: "video", link: null },
        { name: "audio", link: null },
    ]);
    assert.deepEqual([...desired], ["image", "image_2", "image_3", "video", "audio"]);
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
