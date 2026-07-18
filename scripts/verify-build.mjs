// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

import { renderPdf } from "../netlify/functions/_shared/pdf.mjs";

const html = await readFile(new URL("../public/index.html", import.meta.url), "utf8");
assert.match(html, /<title>Ontime Cue Sheet<\/title>/);
assert.doesNotMatch(html, /\{\{/);

const pdf = await renderPdf([], "Deployment smoke test", {
  versionCode: "20260718-1200",
});
assert.equal(pdf.subarray(0, 4).toString(), "%PDF");

console.log(`Verified static app and ${pdf.length}-byte PDF renderer output.`);
