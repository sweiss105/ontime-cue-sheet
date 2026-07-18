// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

import { fetchCurrentRundown, OntimeError } from "./_shared/ontime.mjs";
import {
  contentDisposition,
  normalizeVersionCode,
  renderPdf,
} from "./_shared/pdf.mjs";
import { json, methodNotAllowed } from "./_shared/responses.mjs";

export default async function generate(request) {
  if (request.method !== "POST") return methodNotAllowed();
  try {
    const form = await request.formData();
    const rundown = await fetchCurrentRundown(form.get("base_url"), {
      authHeader: process.env.ONTIME_AUTH_HEADER,
      authValue: process.env.ONTIME_AUTH_VALUE,
    });
    const includeSkipped = form.get("include_skipped") === "true";
    const events = includeSkipped
      ? rundown.events
      : rundown.events.filter((event) => !event.skip);
    const allowedFields = new Set(rundown.custom_fields);
    const fieldsConfigured = form.get("fields_configured") === "true";
    const requestedFields = fieldsConfigured
      ? form.getAll("selected_fields")
      : form.getAll("selected_custom_fields");
    const selectedFields = [
      ...new Set(requestedFields.map(String).filter((field) => allowedFields.has(field))),
    ];
    const title = String(form.get("title") || "Cue Sheet");
    const versionCode = normalizeVersionCode(form.get("version_code"));
    const pdf = await renderPdf(events, title, {
      paperSize: ["Letter", "A4"].includes(form.get("paper_size"))
        ? form.get("paper_size")
        : "Letter",
      orientation: ["portrait", "landscape"].includes(form.get("orientation"))
        ? form.get("orientation")
        : "landscape",
      includeNotes: form.get("include_notes") === "true",
      selectedFields,
      versionCode,
    });
    return new Response(pdf, {
      status: 200,
      headers: {
        "Cache-Control": "no-store",
        "Content-Disposition": contentDisposition(title, versionCode),
        "Content-Length": String(pdf.length),
        "Content-Type": "application/pdf",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch (error) {
    const message = error instanceof OntimeError ? error.message : "PDF generation failed";
    return json({ ok: false, error: message }, error instanceof OntimeError ? 502 : 500);
  }
}

export const config = {
  path: "/generate",
  method: "POST",
};
