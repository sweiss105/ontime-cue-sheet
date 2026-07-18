// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

import { fetchCurrentRundown, OntimeError } from "./_shared/ontime.mjs";
import { json, methodNotAllowed } from "./_shared/responses.mjs";

export default async function connectionTest(request) {
  if (request.method !== "POST") return methodNotAllowed();
  try {
    const form = await request.formData();
    const rundown = await fetchCurrentRundown(form.get("base_url"), {
      authHeader: process.env.ONTIME_AUTH_HEADER,
      authValue: process.env.ONTIME_AUTH_VALUE,
    });
    return json({ ok: true, event_count: rundown.events.length });
  } catch (error) {
    const message = error instanceof OntimeError ? error.message : "Unable to load rundown";
    return json({ ok: false, error: message }, 502);
  }
}

export const config = {
  path: "/connection-test",
  method: "POST",
};
