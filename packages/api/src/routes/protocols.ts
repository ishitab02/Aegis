/**
 * Protocol management routes — register, list, update monitored protocols.
 *
 * GET   /                  — list all protocols
 * GET   /:address          — get protocol details
 * POST  /                  — register new protocol
 * PATCH /:address          — update thresholds / name / active
 * GET   /:address/status   — circuit breaker status (on-chain read)
 */

import { Hono } from "hono";
import { insertProtocol, getProtocol, listProtocols, updateProtocol } from "../db/index.js";
import { getCircuitBreakerState } from "../services/contractReader.js";

const protocols = new Hono();

// GET / — list all protocols
protocols.get("/", (c) => {
  const activeOnly = c.req.query("active") === "true";
  const rows = listProtocols(activeOnly);
  return c.json({ protocols: rows });
});

// GET /:address — single protocol
protocols.get("/:address", (c) => {
  const row = getProtocol(c.req.param("address"));
  if (!row) return c.json({ error: "Protocol not found" }, 404);
  return c.json(row);
});

// POST / — register a new protocol
protocols.post("/", async (c) => {
  const body = await c.req.json().catch(() => null);
  if (!body) return c.json({ error: "Invalid JSON body" }, 400);

  const { address, name, alert_threshold, breaker_threshold } = body;

  if (!address || !name) {
    return c.json({ error: "address and name are required" }, 400);
  }

  // Prevent duplicates
  if (getProtocol(address)) {
    return c.json({ error: "Protocol already registered" }, 409);
  }

  const row = insertProtocol(address, name, alert_threshold ?? 10, breaker_threshold ?? 20);
  return c.json(row, 201);
});

// PATCH /:address — partial update
protocols.patch("/:address", async (c) => {
  const address = c.req.param("address");

  if (!getProtocol(address)) {
    return c.json({ error: "Protocol not found" }, 404);
  }

  const body = await c.req.json().catch(() => null);
  if (!body) return c.json({ error: "Invalid JSON body" }, 400);

  const updated = updateProtocol(address, {
    name: body.name,
    alert_threshold: body.alert_threshold,
    breaker_threshold: body.breaker_threshold,
    active: body.active,
  });

  return c.json(updated);
});

// GET /:address/status — circuit breaker status (live on-chain)
protocols.get("/:address/status", async (c) => {
  const address = c.req.param("address");
  const protocol = getProtocol(address);

  const breakerState = await getCircuitBreakerState(address);

  return c.json({
    address,
    registered: !!protocol,
    protocol: protocol ?? null,
    circuitBreaker: breakerState,
    timestamp: Math.floor(Date.now() / 1000),
  });
});

export { protocols };
