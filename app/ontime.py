from __future__ import annotations

from typing import Any

import httpx


class OntimeError(RuntimeError):
    pass


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

    for key in ("events", "rundown", "entries", "data"):
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict) and item.get("type", "event").lower() == "event"]
        if isinstance(value, dict):
            try:
                return extract_events(value)
            except OntimeError:
                pass
    raise OntimeError("No events were found in the current rundown")


async def fetch_current_rundown(
    base_url: str,
    auth_header: str | None = None,
    auth_value: str | None = None,
) -> list[dict[str, Any]]:
    headers = {}
    if auth_header and auth_value:
        headers[auth_header] = auth_value
    url = f"{base_url.rstrip('/')}/data/rundowns/current"
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            if "application/json" not in response.headers.get("content-type", ""):
                raise OntimeError("Ontime returned a non-JSON response; check the stage URL and login requirements")
            return extract_events(response.json())
    except httpx.HTTPError as exc:
        raise OntimeError(f"Could not read the Ontime rundown: {exc}") from exc

