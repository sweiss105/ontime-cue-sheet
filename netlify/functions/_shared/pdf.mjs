// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

import { dirname, resolve, sep } from "node:path";

import pdfmake from "pdfmake";
import robotoFonts from "pdfmake/fonts/Roboto.js";

const VERSION_CODE = /^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})$/;
const HEX_COLOUR = /^#([0-9a-f]{6})$/i;

pdfmake.addFonts(robotoFonts);
const fontDirectory = `${resolve(dirname(robotoFonts.Roboto.normal))}${sep}`;
pdfmake.setLocalAccessPolicy((path) => resolve(path).startsWith(fontDirectory));
pdfmake.setUrlAccessPolicy(() => false);
pdfmake.addTableLayouts({
  cueSheet: {
    hLineWidth(index, node) {
      return index > 1 && index < node.table.body.length ? 0.5 : 0;
    },
    hLineColor() {
      return "#CFD3D5";
    },
    vLineWidth() {
      return 0;
    },
    paddingLeft() {
      return 6;
    },
    paddingRight() {
      return 6;
    },
    paddingTop(index) {
      return index === 0 ? 6 : 5;
    },
    paddingBottom(index) {
      return index === 0 ? 6 : 5;
    },
  },
});

export function clock(value) {
  const totalSeconds = Math.floor((Number(value) || 0) / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return [hours, minutes, seconds].map((part) => String(part).padStart(2, "0")).join(":");
}
export function normalizeVersionCode(value = "", now = new Date()) {
  const candidate = String(value ?? "").trim();
  const match = VERSION_CODE.exec(candidate);
  if (match) {
    const [, year, month, day, hour, minute] = match.map(Number);
    const date = new Date(Date.UTC(year, month - 1, day, hour, minute));
    if (
      date.getUTCFullYear() === year &&
      date.getUTCMonth() === month - 1 &&
      date.getUTCDate() === day &&
      date.getUTCHours() === hour &&
      date.getUTCMinutes() === minute
    ) {
      return candidate;
    }
  }
  const pad = (part) => String(part).padStart(2, "0");
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}`;
}

export function pdfFilename(title, versionCode = "") {
  let name = String(title ?? "")
    .replace(/[<>:"/\\|?*\u0000-\u001f]/g, "-")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/[. ]+$/g, "");
  name = name
    .replace(/\.pdf$/i, "")
    .replace(/[. ]+$/g, "")
    .replace(/-CUESHEET$/i, "")
    .replace(/[. ]+$/g, "")
    .slice(0, 120)
    .replace(/[. ]+$/g, "");
  return `${name || "cue-sheet"}-CUESHEET-${normalizeVersionCode(versionCode)}.pdf`;
}

export function cueColour(value) {
  const match = HEX_COLOUR.exec(String(value ?? "").trim());
  return match ? `#${match[1].toUpperCase()}` : "";
}

function colourChannels(value) {
  const colour = cueColour(value);
  if (!colour) return [255, 255, 255];
  return [1, 3, 5].map((offset) => Number.parseInt(colour.slice(offset, offset + 2), 16));
}

function blend(base, overlay, opacity) {
  return base.map((channel, index) =>
    Math.round(channel * (1 - opacity) + overlay[index] * opacity),
  );
}

function rgbHex(channels) {
  return `#${channels.map((channel) => channel.toString(16).padStart(2, "0")).join("")}`;
}

export function cueTint(value, alternating = false) {
  let channels = blend([255, 255, 255], colourChannels(value), cueColour(value) ? 0.15 : 0);
  if (alternating) channels = blend(channels, [255, 255, 255], 0.05);
  return rgbHex(channels).toUpperCase();
}

function safeText(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
  return String(value);
}

function generatedAt(versionCode) {
  return `${versionCode.slice(0, 4)}-${versionCode.slice(4, 6)}-${versionCode.slice(6, 8)} ${versionCode.slice(9, 11)}:${versionCode.slice(11, 13)}`;
}

function headerCell(text) {
  return {
    text: text.toUpperCase(),
    bold: true,
    color: "#FFFFFF",
    fillColor: "#1D2326",
    fontSize: 7,
    noWrap: true,
  };
}

function bodyCell(content, event, rowIndex, overrides = {}) {
  const skipped = Boolean(event.skip);
  return {
    text: safeText(content),
    fillColor: cueTint(event.colour, rowIndex % 2 === 1),
    color: skipped ? "#777777" : "#171717",
    decoration: skipped ? "lineThrough" : undefined,
    fontSize: 8.5,
    ...overrides,
  };
}

function titleCell(event, rowIndex, includeNotes) {
  const skipped = Boolean(event.skip);
  const stack = [
    {
      text: safeText(event.title),
      bold: true,
      color: skipped ? "#777777" : "#171717",
      decoration: skipped ? "lineThrough" : undefined,
      fontSize: 8.5,
    },
  ];
  if (includeNotes && event.note) {
    stack.push({
      text: safeText(event.note),
      italics: true,
      color: skipped ? "#888888" : "#505659",
      decoration: skipped ? "lineThrough" : undefined,
      fontSize: 7,
      margin: [0, 2, 0, 0],
    });
  }
  return { stack, fillColor: cueTint(event.colour, rowIndex % 2 === 1) };
}

export async function renderPdf(events, title, options = {}) {
  const paperSize = ["Letter", "A4"].includes(options.paperSize) ? options.paperSize : "Letter";
  const orientation = options.orientation === "portrait" ? "portrait" : "landscape";
  const selectedFields = [...new Set((options.selectedFields || []).filter((field) => field !== "Notes"))];
  const includeNotes = Boolean(options.includeNotes || options.selectedFields?.includes("Notes"));
  const versionCode = normalizeVersionCode(options.versionCode);
  const safeTitle = String(title ?? "").trim() || "Cue Sheet";
  const headers = ["Cue", "Start", "Duration", "Title", ...selectedFields];
  const rows = events.map((event, rowIndex) => [
    bodyCell(event.cue || "—", event, rowIndex, { bold: true, noWrap: true }),
    bodyCell(clock(event.timeStart), event, rowIndex, { noWrap: true }),
    bodyCell(clock(event.duration), event, rowIndex, { noWrap: true }),
    titleCell(event, rowIndex, includeNotes),
    ...selectedFields.map((field) => bodyCell(event.custom?.[field], event, rowIndex)),
  ]);
  const titleSize = safeTitle.length > 54 ? 14 : safeTitle.length > 40 ? 17 : 22;

  const definition = {
    pageSize: paperSize,
    pageOrientation: orientation,
    pageMargins: [18, 62, 18, 28],
    info: { title: safeTitle, author: "Ontime Cue Sheet" },
    defaultStyle: { font: "Roboto", fontSize: 8.5, color: "#171717" },
    header() {
      return {
        margin: [18, 16, 18, 0],
        stack: [
          {
            columns: [
              { text: safeTitle, bold: true, fontSize: titleSize, noWrap: true },
              {
                width: 126,
                text: `Generated ${generatedAt(versionCode)}\n${events.length} cues`,
                alignment: "right",
                color: "#555555",
                fontSize: 8,
                lineHeight: 1.05,
              },
            ],
            columnGap: 10,
          },
          {
            canvas: [
              { type: "line", x1: 0, y1: 7, x2: orientation === "landscape" ? (paperSize === "A4" ? 805.89 : 756) : (paperSize === "A4" ? 559.28 : 576), y2: 7, lineWidth: 2, lineColor: "#171717" },
            ],
          },
        ],
      };
    },
    footer(currentPage, pageCount) {
      return {
        text: `${versionCode} - Page ${currentPage} of ${pageCount}`,
        alignment: "right",
        color: "#666666",
        fontSize: 8,
        margin: [18, 0, 18, 0],
      };
    },
    content: [
      {
        layout: "cueSheet",
        table: {
          headerRows: 1,
          dontBreakRows: true,
          keepWithHeaderRows: 1,
          widths: ["auto", "auto", "auto", "*", ...selectedFields.map(() => "*")],
          body: [headers.map(headerCell), ...rows],
        },
      },
    ],
  };

  const buffer = await pdfmake.createPdf(definition).getBuffer();
  return Buffer.from(buffer);
}

export function contentDisposition(title, versionCode) {
  const filename = pdfFilename(title, versionCode);
  const asciiStem = filename
    .slice(0, -4)
    .normalize("NFKD")
    .replace(/[^\x20-\x7e]/g, "")
    .trim()
    .replace(/[. ]+$/g, "");
  const asciiFilename = `${asciiStem || "cue-sheet-CUESHEET"}.pdf`;
  const encoded = encodeURIComponent(filename).replace(/[!'()*]/g, (character) =>
    `%${character.charCodeAt(0).toString(16).toUpperCase()}`,
  );
  return `attachment; filename="${asciiFilename}"; filename*=UTF-8''${encoded}`;
}
