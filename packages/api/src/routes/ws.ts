// SSE-based real-time alert stream.
// broadcast() is exported so alert routes can push to all connected clients.

import { Hono } from "hono";
import { streamSSE } from "hono/streaming";
import type { AlertRow } from "../db/index.js";

type Subscriber = (alert: AlertRow) => void;

const subscribers = new Set<Subscriber>();

export function broadcast(alert: AlertRow): void {
  for (const cb of subscribers) {
    try {
      cb(alert);
    } catch {
      subscribers.delete(cb);
    }
  }
}

export function subscriberCount(): number {
  return subscribers.size;
}

const ws = new Hono();

ws.get("/", (c) => {
  return streamSSE(c, async (stream) => {
    // 30s heartbeat to keep connection alive
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

    await stream.writeSSE({
      data: JSON.stringify({
        type: "connected",
        subscribers: subscribers.size,
        timestamp: Math.floor(Date.now() / 1000),
      }),
      event: "system",
      id: "0",
    });

    stream.onAbort(() => {
      subscribers.delete(onAlert);
      clearInterval(heartbeat);
    });

    // block until client disconnects
    await new Promise(() => {});
  });
});

export { ws };
