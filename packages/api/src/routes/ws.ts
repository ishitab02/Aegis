/**
 * WebSocket route for real-time alert streaming.
 *
 * Clients connect to  ws://localhost:3000/api/v1/ws
 * and receive JSON-encoded alerts as they are created.
 *
 * The module also exports `broadcast()` so the alerts route can push
 * new alerts to every connected client instantly.
 *
 * Implementation note: Hono's Node.js adapter doesn't expose native WS
 * support, so we use a lightweight in-process pub/sub with Server-Sent
 * Events (SSE) instead — works out of the box with fetch/EventSource
 * in every browser and requires no extra dependencies.
 *
 * Endpoint:
 *   GET /api/v1/ws   →  text/event-stream (SSE)
 */

import { Hono } from "hono";
import { streamSSE } from "hono/streaming";
import type { AlertRow } from "../db/index.js";

// ---- In-memory subscriber list ----

type Subscriber = (alert: AlertRow) => void;

const subscribers = new Set<Subscriber>();

/** Push an alert to every connected SSE client. */
export function broadcast(alert: AlertRow): void {
  for (const cb of subscribers) {
    try {
      cb(alert);
    } catch {
      subscribers.delete(cb);
    }
  }
}

/** Current number of live connections (useful for health checks). */
export function subscriberCount(): number {
  return subscribers.size;
}

// ---- SSE route ----

const ws = new Hono();

ws.get("/", (c) => {
  return streamSSE(c, async (stream) => {
    // Send a heartbeat comment every 30s to keep the connection alive
    const heartbeat = setInterval(() => {
      stream.writeSSE({ data: "", event: "ping", id: "" }).catch(() => {
        clearInterval(heartbeat);
      });
    }, 30_000);

    // Register subscriber
    const onAlert: Subscriber = (alert) => {
      stream
        .writeSSE({
          data: JSON.stringify(alert),
          event: "alert",
          id: alert.id,
        })
        .catch(() => {
          /* stream closed */
        });
    };

    subscribers.add(onAlert);

    // Send initial connection confirmation
    await stream.writeSSE({
      data: JSON.stringify({
        type: "connected",
        subscribers: subscribers.size,
        timestamp: Math.floor(Date.now() / 1000),
      }),
      event: "system",
      id: "0",
    });

    // Keep stream open until the client disconnects
    stream.onAbort(() => {
      subscribers.delete(onAlert);
      clearInterval(heartbeat);
    });

    // Block forever (SSE stays open)
    await new Promise(() => {});
  });
});

export { ws };
