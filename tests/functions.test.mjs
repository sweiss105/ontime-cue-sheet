// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

import assert from "node:assert/strict";
import test from "node:test";

import generate from "../netlify/functions/generate.mjs";
import health from "../netlify/functions/health.mjs";
import preview from "../netlify/functions/preview.mjs";
import { EVENT, ontimeResponses } from "./fixtures.mjs";

function request(path, entries) {
  const form = new FormData();
  entries.forEach(([key, value]) => form.append(key, value));
  return new Request(`http://localhost${path}`, { method: "POST", body: form });
}

test("health identifies the Netlify runtime", async () => {
  const response = await health();
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { status: "ok", platform: "netlify" });
});
test("preview returns project title, available fields, and filtered events", async (context) => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = ontimeResponses([EVENT, { ...EVENT, id: "evt-2", skip: true }]);
  context.after(() => {
    globalThis.fetch = originalFetch;
  });
  const response = await preview(
    request("/preview", [["base_url", "https://cloud.getontime.no/my-stage?token=secret"]]),
  );
  assert.equal(response.status, 200);
  const data = await response.json();
  assert.equal(data.title, "WCTC Underestimated to Unstoppable");
  assert.deepEqual(data.custom_fields, ["Audio", "Video"]);
  assert.equal(data.events.length, 1);
});

test("generate preserves dragged field order and filename versioning", async (context) => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = ontimeResponses();
  context.after(() => {
    globalThis.fetch = originalFetch;
  });
  const response = await generate(
    request("/generate", [
      ["base_url", "https://cloud.getontime.no/my-stage?token=secret"],
      ["title", "Fall Kick Off 2026"],
      ["paper_size", "Letter"],
      ["orientation", "landscape"],
      ["include_notes", "true"],
      ["fields_configured", "true"],
      ["selected_fields", "Video"],
      ["selected_fields", "Audio"],
      ["version_code", "20260715-1310"],
    ]),
  );
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("content-type"), "application/pdf");
  assert.match(
    response.headers.get("content-disposition"),
    /Fall Kick Off 2026-CUESHEET-20260715-1310\.pdf/,
  );
  const pdf = Buffer.from(await response.arrayBuffer());
  assert.equal(pdf.subarray(0, 4).toString(), "%PDF");
});
