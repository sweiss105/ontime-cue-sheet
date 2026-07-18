// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

import { mkdir, writeFile } from "node:fs/promises";

import { renderPdf } from "../netlify/functions/_shared/pdf.mjs";

const colours = ["#339E4E", "#B946C2", "#3478C7", "#E2A72E", ""];
const events = Array.from({ length: 60 }, (_, index) => ({
  type: "event",
  id: `evt-${index}`,
  cue: `${Math.floor(index / 6) + 1}.${(index % 6) + 1}`,
  title:
    index % 7 === 0
      ? `Cue ${index + 1} with a longer production title that wraps naturally`
      : `Cue ${index + 1}`,
  note: index % 4 === 0 ? "Smaller italic production note under the cue title" : "",
  timeStart: 32_400_000 + index * 180_000,
  duration: index % 3 === 0 ? 180_000 : 90_000,
  colour: colours[index % colours.length],
  custom: {
    Audio: index % 2 === 0 ? "Playback and microphone check" : "",
    Video: index % 3 === 0 ? "Presentation roll" : "",
    Lighting: index % 5 === 0 ? "Stage look 2" : "",
  },
}));

const output = new URL("../tmp/pdfs/netlify-migration-qa.pdf", import.meta.url);
await mkdir(new URL("../tmp/pdfs/", import.meta.url), { recursive: true });
await writeFile(
  output,
  await renderPdf(events, "Netlify Migration Cue Sheet", {
    includeNotes: true,
    selectedFields: ["Audio", "Video", "Lighting"],
    versionCode: "20260718-1200",
  }),
);

console.log(output.pathname);
