// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

export function json(data, status = 200) {
  return Response.json(data, {
    status,
    headers: {
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
export function methodNotAllowed() {
  return json({ ok: false, error: "Method not allowed" }, 405);
}
