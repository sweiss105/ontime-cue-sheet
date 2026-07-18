// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

export class OntimeError extends Error {}

export const ONTIME_CLOUD_HOST = "cloud.getontime.no";
export const MAX_ONTIME_RESPONSE_BYTES = 5 * 1024 * 1024;

export function validateOntimeUrl(baseUrl) {
  const rawUrl = String(baseUrl ?? "").trim();
  if (!rawUrl || rawUrl.length > 4096) {
    throw new OntimeError("Enter a valid Ontime Cloud stage or Companion share URL");
  }

  let parsed;
  try {
    parsed = new URL(rawUrl);
  } catch {
    throw new OntimeError("Enter a valid Ontime Cloud stage or Companion share URL");
  }

  const hostname = parsed.hostname.toLowerCase().replace(/\.$/, "");
  if (parsed.protocol !== "https:" || hostname !== ONTIME_CLOUD_HOST) {
    throw new OntimeError(`Only HTTPS Ontime Cloud URLs from ${ONTIME_CLOUD_HOST} are supported`);
  }
  if (parsed.username || parsed.password || (parsed.port && parsed.port !== "443")) {
    throw new OntimeError("Ontime Cloud URLs cannot contain credentials or a custom port");
  }
  if (parsed.hash) {
    throw new OntimeError("Remove the fragment from the Ontime Cloud URL and try again");
  }
  if (!parsed.pathname.replaceAll("/", "")) {
    throw new OntimeError("The Ontime Cloud URL must include a stage identifier");
  }
}
export function buildDataUrl(baseUrl, resource) {
  const parsed = new URL(String(baseUrl).trim());
  parsed.pathname = `${parsed.pathname.replace(/\/+$/, "")}/data/${String(resource).replace(/^\/+|\/+$/g, "")}/`;
  parsed.hash = "";
  return parsed.toString();
}

export function buildRundownUrl(baseUrl) {
  return buildDataUrl(baseUrl, "rundowns/current");
}

export function buildProjectUrl(baseUrl) {
  return buildDataUrl(baseUrl, "project");
}

function unwrapPayload(data) {
  return data && typeof data === "object" && !Array.isArray(data) && "payload" in data
    ? data.payload
    : data;
}

export function extractEvents(data) {
  const unwrapped = unwrapPayload(data);
  if (Array.isArray(unwrapped)) {
    return unwrapped.filter((item) => item && typeof item === "object" && item.type === "event");
  }
  if (!unwrapped || typeof unwrapped !== "object") {
    throw new OntimeError("Ontime returned an unexpected rundown format");
  }

  if (unwrapped.entries && typeof unwrapped.entries === "object" && !Array.isArray(unwrapped.entries)) {
    const order = Array.isArray(unwrapped.flatOrder)
      ? unwrapped.flatOrder
      : Object.keys(unwrapped.entries);
    return order
      .map((entryId) => unwrapped.entries[entryId])
      .filter(
        (entry) =>
          entry &&
          typeof entry === "object" &&
          String(entry.type ?? "event").toLowerCase() === "event",
      );
  }

  for (const key of ["events", "rundown", "data"]) {
    const value = unwrapped[key];
    if (Array.isArray(value)) {
      return value.filter(
        (item) =>
          item && typeof item === "object" && String(item.type ?? "event").toLowerCase() === "event",
      );
    }
    if (value && typeof value === "object") {
      try {
        return extractEvents(value);
      } catch (error) {
        if (!(error instanceof OntimeError)) throw error;
      }
    }
  }
  throw new OntimeError("No events were found in the current rundown");
}

export function extractProjectTitle(data) {
  const unwrapped = unwrapPayload(data);
  if (!unwrapped || typeof unwrapped !== "object" || Array.isArray(unwrapped)) return "";
  return String(unwrapped.title ?? "").trim();
}

export function extractRundown(data, projectData = null) {
  const unwrapped = unwrapPayload(data);
  const events = extractEvents(unwrapped);
  const rundownTitle =
    unwrapped && typeof unwrapped === "object" && !Array.isArray(unwrapped)
      ? String(unwrapped.title ?? "").trim()
      : "";
  const title = extractProjectTitle(projectData) || rundownTitle;
  const customFields = [];
  for (const event of events) {
    const custom = event.custom;
    if (!custom || typeof custom !== "object" || Array.isArray(custom)) continue;
    for (const field of Object.keys(custom)) {
      if (!customFields.includes(field)) customFields.push(field);
    }
  }
  return { title, rundown_title: rundownTitle, events, custom_fields: customFields };
}

async function readJsonResponse(response, tooLargeMessage) {
  const declaredSize = Number(response.headers.get("content-length") || 0);
  if (declaredSize > MAX_ONTIME_RESPONSE_BYTES) throw new OntimeError(tooLargeMessage);

  const reader = response.body?.getReader();
  if (!reader) return response.json();
  const chunks = [];
  let total = 0;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > MAX_ONTIME_RESPONSE_BYTES) {
      await reader.cancel();
      throw new OntimeError(tooLargeMessage);
    }
    chunks.push(value);
  }
  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return JSON.parse(new TextDecoder().decode(bytes));
}

export async function fetchCurrentRundown(baseUrl, options = {}) {
  validateOntimeUrl(baseUrl);
  const headers = {};
  if (options.authHeader && options.authValue) headers[options.authHeader] = options.authValue;
  const requestOptions = {
    headers,
    redirect: "manual",
    signal: AbortSignal.timeout(20_000),
  };

  try {
    const [rundownResult, projectResult] = await Promise.allSettled([
      fetch(buildRundownUrl(baseUrl), requestOptions),
      fetch(buildProjectUrl(baseUrl), requestOptions),
    ]);
    if (rundownResult.status === "rejected") throw rundownResult.reason;
    const rundownResponse = rundownResult.value;
    if (rundownResponse.status >= 300 && rundownResponse.status < 400) {
      throw new OntimeError(
        "Ontime redirected the request unexpectedly; check the stage or Companion share URL",
      );
    }
    if ([401, 403].includes(rundownResponse.status)) {
      throw new OntimeError(
        "Ontime rejected the connection. For a password-protected stage, paste an authenticated Companion share link from Ontime's Sharing and reporting settings.",
      );
    }
    if (!rundownResponse.ok) {
      throw new OntimeError(`Ontime returned HTTP ${rundownResponse.status}`);
    }
    if (!rundownResponse.headers.get("content-type")?.toLowerCase().includes("application/json")) {
      throw new OntimeError(
        "Ontime returned a non-JSON response; check the stage URL and login requirements",
      );
    }
    const rundownData = await readJsonResponse(
      rundownResponse,
      "The Ontime rundown response was too large to process safely",
    );

    let projectData = null;
    if (projectResult.status === "fulfilled") {
      const projectResponse = projectResult.value;
      if (
        projectResponse.ok &&
        projectResponse.headers.get("content-type")?.toLowerCase().includes("application/json")
      ) {
        try {
          projectData = await readJsonResponse(
            projectResponse,
            "The Ontime project response was too large to process safely",
          );
        } catch {
          projectData = null;
        }
      }
    }
    return extractRundown(rundownData, projectData);
  } catch (error) {
    if (error instanceof OntimeError) throw error;
    throw new OntimeError("Could not read the Ontime rundown; check the stage URL and try again");
  }
}
