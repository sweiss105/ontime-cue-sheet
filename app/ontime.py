from __future__ import annotations

from typing import Any, TypedDict
from urllib.parse import urlsplit, urlunsplit

import httpx


class OntimeError(RuntimeError):
    pass


class RundownData(TypedDict):
    title: str
    events: list[dict[str, Any]]
    custom_fields: list[str]


def build_rundown_url(base_url: str) -> str:
    """Append the data endpoint without losing an authenticated share-link token."""
    parsed = urlsplit(base_url.strip())
    path = f"{parsed.path.rstrip('/')}/data/rundowns/current/"
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, ""))


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


def extract_rundown(data: Any) -> RundownData:
    """Extract printable rundown metadata while preserving event and field order."""
    unwrapped = _unwrap_payload(data)
    events = extract_events(unwrapped)
    title = unwrapped.get("title", "") if isinstance(unwrapped, dict) else ""
    custom_fields: list[str] = []
    for event in events:
        custom = event.get("custom")
        if not isinstance(custom, dict):
            continue
        for field in custom:
            if field not in custom_fields:
                custom_fields.append(field)
    return {"title": str(title), "events": events, "custom_fields": custom_fields}


async def fetch_current_rundown(
    base_url: str,
    auth_header: str | None = None,
    auth_value: str | None = None,
) -> RundownData:
    headers = {}
    if auth_header and auth_value:
        headers[auth_header] = auth_value
    url = build_rundown_url(base_url)
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 401:
                raise OntimeError(
                    "Ontime rejected the connection. For a password-protected stage, paste an "
                    "authenticated Companion share link from Ontime's Sharing and reporting settings."
                )
            response.raise_for_status()
            if "application/json" not in response.headers.get("content-type", ""):
                raise OntimeError("Ontime returned a non-JSON response; check the stage URL and login requirements")
            return extract_rundown(response.json())
    except OntimeError:
        raise
    except httpx.HTTPError as exc:
        raise OntimeError(f"Could not read the Ontime rundown: {exc}") from exc
