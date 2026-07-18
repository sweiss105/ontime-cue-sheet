// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { getDocument } from "pdfjs-dist/legacy/build/pdf.mjs";

import {
  clock,
  contentDisposition,
  cueColour,
  cueTint,
  normalizeVersionCode,
  pdfFilename,
  renderPdf,
} from "../netlify/functions/_shared/pdf.mjs";
import { EVENT } from "./fixtures.mjs";

const standardFontDataUrl = `${fileURLToPath(
  new URL("../node_modules/pdfjs-dist/standard_fonts/", import.meta.url),
)}/`;

async function pdfPages(buffer) {
  const document = await getDocument({
    data: new Uint8Array(buffer),
    standardFontDataUrl,
  }).promise;
  const pages = [];
  for (let index = 1; index <= document.numPages; index += 1) {
    const page = await document.getPage(index);
    const content = await page.getTextContent();
    pages.push(content.items.map((item) => item.str).join(" "));
  }
  return pages;
}

test("formats clocks, colours, version codes, and portable filenames", () => {
  assert.equal(clock(36_061_000), "10:01:01");
  assert.equal(cueColour("#339e4e"), "#339E4E");
  assert.equal(cueColour("invalid"), "");
  assert.equal(cueTint("#339E4E"), "#E0F0E4");
  assert.equal(normalizeVersionCode("20260715-1310"), "20260715-1310");
  assert.notEqual(normalizeVersionCode("20261340-9999"), "20261340-9999");
  assert.equal(
    pdfFilename("WCTC Underestimated to Unstoppable", "20260715-1310"),
    "WCTC Underestimated to Unstoppable-CUESHEET-20260715-1310.pdf",
  );
  assert.equal(
    pdfFilename("  Show / Finale: 2026.pdf  ", "20260715-1310"),
    "Show - Finale- 2026-CUESHEET-20260715-1310.pdf",
  );
  assert.match(contentDisposition("Show", "20260715-1310"), /^attachment; filename="Show-CUESHEET-20260715-1310\.pdf";/);
});

test("renders selected fields, notes, metadata, and A4 portrait PDFs", async () => {
  const pdf = await renderPdf([EVENT], "Selected Fields", {
    paperSize: "A4",
    orientation: "portrait",
    includeNotes: true,
    selectedFields: ["Video"],
    versionCode: "20260715-1310",
  });
  assert.equal(pdf.subarray(0, 4).toString(), "%PDF");
  const [text] = await pdfPages(pdf);
  ["CUE", "START", "DURATION", "TITLE", "VIDEO", "Holding slide", "House opens"].forEach(
    (value) => assert.match(text, new RegExp(value)),
  );
  assert.doesNotMatch(text, /AUDIO|Walk-in playlist/);
  assert.match(text, /Generated 2026-07-15 13:10/);
  assert.match(text, /20260715-1310 - Page 1 of 1/);
});

test("repeats document and table headers and version footer on every PDF page", async () => {
  const events = Array.from({ length: 60 }, (_, index) => ({
    ...EVENT,
    id: `evt-${index}`,
    cue: String(index),
    title: `Cue ${index} with enough text to exercise content-aware wrapping`,
  }));
  const pages = await pdfPages(
    await renderPdf(events, "Long Show Cue Sheet", {
      includeNotes: true,
      selectedFields: ["Audio", "Video"],
      versionCode: "20260715-1310",
    }),
  );
  assert.ok(pages.length > 1);
  pages.forEach((text, index) => {
    ["Long Show Cue Sheet", "CUE", "START", "DURATION", "TITLE", "AUDIO", "VIDEO"].forEach(
      (value) => assert.match(text, new RegExp(value)),
    );
    assert.match(text, new RegExp(`20260715-1310 - Page ${index + 1} of ${pages.length}`));
  });
});
