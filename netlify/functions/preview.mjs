// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

import { fetchCurrentRundown, OntimeError } from "./_shared/ontime.mjs";
import { json, methodNotAllowed } from "./_shared/responses.mjs";

export default async function preview(request) {
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
    return json({
      ok: true,
      title: rundown.title,
      custom_fields: rundown.custom_fields,
      events,
    });
  } catch (error) {
    const message = error instanceof OntimeError ? error.message : "Unable to load rundown";
    return json({ ok: false, error: message }, 502);
  }
}

export const config = {
  path: "/preview",
  method: "POST",
};
