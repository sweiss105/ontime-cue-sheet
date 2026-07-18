// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

import assert from "node:assert/strict";
import test from "node:test";

import {
  buildProjectUrl,
  buildRundownUrl,
  extractEvents,
  extractRundown,
  fetchCurrentRundown,
  OntimeError,
  validateOntimeUrl,
} from "../netlify/functions/_shared/ontime.mjs";
import { EVENT, ontimeResponses } from "./fixtures.mjs";

test("extracts events from Ontime payload and normalized rundown shapes", () => {
  assert.deepEqual(extractEvents({ payload: { events: [EVENT] } }), [EVENT]);
  assert.deepEqual(
    extractEvents({
      flatOrder: ["group-1", "evt-1"],
      entries: {
        "group-1": { type: "group", id: "group-1" },
        "evt-1": EVENT,
      },
    }),
    [EVENT],
  );
  assert.deepEqual(extractEvents({ flatOrder: [], entries: {} }), []);
});
test("uses project title with rundown title as fallback and preserves field order", () => {
  const rundown = extractRundown(
    { title: "Fall Kick Off 2026", flatOrder: ["evt-1"], entries: { "evt-1": EVENT } },
    { title: "WCTC Underestimated to Unstoppable" },
  );
  assert.equal(rundown.title, "WCTC Underestimated to Unstoppable");
  assert.equal(rundown.rundown_title, "Fall Kick Off 2026");
  assert.deepEqual(rundown.custom_fields, ["Audio", "Video"]);
  assert.equal(extractRundown({ title: "Fallback", events: [EVENT] }).title, "Fallback");
});

test("preserves cloud prefix and companion token in data URLs", () => {
  assert.equal(
    buildRundownUrl("https://cloud.getontime.no/my-stage/?token=secret"),
    "https://cloud.getontime.no/my-stage/data/rundowns/current/?token=secret",
  );
  assert.equal(
    buildProjectUrl("https://cloud.getontime.no/my-stage/?token=secret"),
    "https://cloud.getontime.no/my-stage/data/project/?token=secret",
  );
});

test("accepts only safe Ontime Cloud share URLs", () => {
  assert.doesNotThrow(() =>
    validateOntimeUrl("https://cloud.getontime.no/my-stage?token=secret"),
  );
  const unsafeUrls = [
    "http://cloud.getontime.no/my-stage",
    "https://cloud.getontime.no.evil.example/my-stage",
    "https://user:password@cloud.getontime.no/my-stage",
    "https://cloud.getontime.no:8443/my-stage",
    "https://cloud.getontime.no/my-stage#fragment",
    "https://cloud.getontime.no/",
  ];
  unsafeUrls.forEach((url) => assert.throws(() => validateOntimeUrl(url), OntimeError));
});

test("fetches rundown and project metadata without following redirects", async (context) => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = ontimeResponses();
  context.after(() => {
    globalThis.fetch = originalFetch;
  });

  const rundown = await fetchCurrentRundown(
    "https://cloud.getontime.no/my-stage?token=secret",
  );
  assert.equal(rundown.title, "WCTC Underestimated to Unstoppable");
  assert.equal(rundown.events.length, 1);
});
