// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const html = await readFile(new URL("../public/index.html", import.meta.url), "utf8");

test("static UI preserves import, draggable fields, preview pagination, and versioned downloads", () => {
  [
    ">Import Cues</button>",
    'class="field-option" draggable="true"',
    "input.name='selected_fields'",
    "fieldList.addEventListener('dragstart'",
    "function finishFieldDrag()",
    'id="page-nav"',
    "function paginateEvents(events)",
    "usedHeight+rowHeight>availableTableHeight",
    "function versionCode(date=new Date())",
    "function pdfFilename(value,version)",
    "data.set('version_code',version)",
    "link.download=pdfFilename(title.value,version)",
  ].forEach((value) => assert.ok(html.includes(value), `Expected index.html to include ${value}`));
  assert.ok(html.includes("aspect-ratio:11/8.5; padding:24px;"));
  assert.ok(html.includes("tbody tr:nth-child(even) td { background-color:rgba(255,255,255,.05); }"));
  assert.ok(html.includes('style="color:#000000;background-color:${cueTint(colour)}"'));
  assert.ok(html.includes('class="cue-note"'));
  assert.doesNotMatch(html, /\{\{/);
});
