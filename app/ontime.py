# Copyright 2026 Steve Weiss
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
from typing import Any, TypedDict
from urllib.parse import urlsplit, urlunsplit

import httpx


class OntimeError(RuntimeError):
    pass


ONTIME_CLOUD_HOST = "cloud.getontime.no"
MAX_ONTIME_RESPONSE_BYTES = 5 * 1024 * 1024


class RundownData(TypedDict):
    title: str
    rundown_title: str
    events: list[dict[str, Any]]
    custom_fields: list[str]


def validate_ontime_url(base_url: str) -> None:
    """Limit the public importer to the hosted Ontime service."""
    raw_url = base_url.strip()
    if not raw_url or len(raw_url) > 4096:
        raise OntimeError("Enter a valid Ontime Cloud stage or Companion share URL")

    parsed = urlsplit(raw_url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise OntimeError("Enter a valid Ontime Cloud stage or Companion share URL") from exc

    hostname = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme.lower() != "https" or hostname != ONTIME_CLOUD_HOST:
        raise OntimeError(f"Only HTTPS Ontime Cloud URLs from {ONTIME_CLOUD_HOST} are supported")
    if parsed.username or parsed.password or (port is not None and port != 443):
        raise OntimeError("Ontime Cloud URLs cannot contain credentials or a custom port")
    if parsed.fragment:
        raise OntimeError("Remove the fragment from the Ontime Cloud URL and try again")
    if not parsed.path.strip("/"):
        raise OntimeError("The Ontime Cloud URL must include a stage identifier")


def build_data_url(base_url: str, resource: str) -> str:
    """Append an Ontime data endpoint without losing an authenticated share-link token."""
    parsed = urlsplit(base_url.strip())
    path = f"{parsed.path.rstrip('/')}/data/{resource.strip('/')}/"
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, ""))


def build_rundown_url(base_url: str) -> str:
    return build_data_url(base_url, "rundowns/current")


def build_project_url(base_url: str) -> str:
    return build_data_url(base_url, "project")


def _unwrap_payload(data: Any) -> Any:
    if isinstance(data, dict) and "payload" in data:
        return data["payload"]
    return data


def extract_events(data: Any) -> list[dict[str, Any]]:
    """Tolerate the common Ontime current-rundown response shapes."""
    data = _unwrap_payload(data)
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict) and item.get("type") == "event"]
    if not isinstance(data, dict):
        raise OntimeError("Ontime returned an unexpected rundown format")

    entries = data.get("entries")
    if isinstance(entries, dict):
        order = data.get("flatOrder")
        if not isinstance(order, list):
            order = list(entries)
        return [
            entry
            for entry_id in order
            if isinstance((entry := entries.get(entry_id)), dict)
            and entry.get("type", "event").lower() == "event"
        ]

    for key in ("events", "rundown", "data"):
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict) and item.get("type", "event").lower() == "event"]
        if isinstance(value, dict):
            try:
                return extract_events(value)
            except OntimeError:
                pass
    raise OntimeError("No events were found in the current rundown")


def extract_project_title(data: Any) -> str:
    unwrapped = _unwrap_payload(data)
    if not isinstance(unwrapped, dict):
        return ""
    return str(unwrapped.get("title") or "").strip()


def extract_rundown(data: Any, project_data: Any = None) -> RundownData:
    """Extract printable rundown metadata while preserving event and field order."""
    unwrapped = _unwrap_payload(data)
    events = extract_events(unwrapped)
    rundown_title = str(unwrapped.get("title") or "").strip() if isinstance(unwrapped, dict) else ""
    title = extract_project_title(project_data) or rundown_title
    custom_fields: list[str] = []
    for event in events:
        custom = event.get("custom")
        if not isinstance(custom, dict):
            continue
        for field in custom:
            if field not in custom_fields:
                custom_fields.append(field)
    return {
        "title": title,
        "rundown_title": rundown_title,
        "events": events,
        "custom_fields": custom_fields,
    }


async def fetch_current_rundown(
    base_url: str,
    auth_header: str | None = None,
    auth_value: str | None = None,
) -> RundownData:
    validate_ontime_url(base_url)
    headers = {}
    if auth_header and auth_value:
        headers[auth_header] = auth_value
    rundown_url = build_rundown_url(base_url)
    project_url = build_project_url(base_url)
    try:
        timeout = httpx.Timeout(20, connect=5)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            rundown_result, project_result = await asyncio.gather(
                client.get(rundown_url, headers=headers),
                client.get(project_url, headers=headers),
                return_exceptions=True,
            )
            if isinstance(rundown_result, Exception):
                raise rundown_result
            if rundown_result.is_redirect:
                raise OntimeError(
                    "Ontime redirected the request unexpectedly; check the stage or Companion share URL"
                )
            if rundown_result.status_code in {401, 403}:
                raise OntimeError(
                    "Ontime rejected the connection. For a password-protected stage, paste an "
                    "authenticated Companion share link from Ontime's Sharing and reporting settings."
                )
            if rundown_result.status_code >= 400:
                raise OntimeError(f"Ontime returned HTTP {rundown_result.status_code}")
            if len(rundown_result.content) > MAX_ONTIME_RESPONSE_BYTES:
                raise OntimeError("The Ontime rundown response was too large to process safely")
            if "application/json" not in rundown_result.headers.get("content-type", ""):
                raise OntimeError("Ontime returned a non-JSON response; check the stage URL and login requirements")
            project_data = None
            if (
                isinstance(project_result, httpx.Response)
                and project_result.is_success
                and len(project_result.content) <= MAX_ONTIME_RESPONSE_BYTES
                and "application/json" in project_result.headers.get("content-type", "")
            ):
                try:
                    project_data = project_result.json()
                except ValueError:
                    project_data = None
            return extract_rundown(rundown_result.json(), project_data)
    except OntimeError:
        raise
    except httpx.HTTPError as exc:
        raise OntimeError("Could not read the Ontime rundown; check the stage URL and try again") from exc
