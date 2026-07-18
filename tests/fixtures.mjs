// Copyright 2026 Steve Weiss
// SPDX-License-Identifier: 0BSD

export const EVENT = {
  type: "event",
  id: "evt-1",
  cue: "A1",
  title: "Doors",
  note: "House opens",
  timeStart: 36_000_000,
  duration: 1_800_000,
  colour: "#339E4E",
  custom: { Audio: "Walk-in playlist", Video: "Holding slide" },
};

export function ontimeResponses(events = [EVENT]) {
  return async (input) => {
    const url = new URL(String(input));
    if (url.pathname.endsWith("/data/project/")) {
      return Response.json({ title: "WCTC Underestimated to Unstoppable" });
    }
    if (url.pathname.endsWith("/data/rundowns/current/")) {
      return Response.json({
        title: "Fall Kick Off 2026",
        flatOrder: events.map((event) => event.id),
        entries: Object.fromEntries(events.map((event) => [event.id, event])),
      });
    }
    return new Response("Not found", { status: 404 });
  };
}
