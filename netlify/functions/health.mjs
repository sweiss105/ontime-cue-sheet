// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

import { json } from "./_shared/responses.mjs";

export default async function health() {
  return json({ status: "ok", platform: "netlify" });
}

export const config = {
  path: "/health",
  method: "GET",
};
