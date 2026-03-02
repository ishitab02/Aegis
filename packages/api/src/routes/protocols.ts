import { Hono } from "hono";
import { insertProtocol, getProtocol, listProtocols, updateProtocol } from "../db/index.js";
import { getCircuitBreakerState } from "../services/contractReader.js";

const protocols = new Hono();

protocols.get("/", (c) => {
  const activeOnly = c.req.query("active") === "true";
  const rows = listProtocols(activeOnly);
  return c.json({ protocols: rows });
});

protocols.get("/:address", (c) => {
  const row = getProtocol(c.req.param("address"));
  if (!row) return c.json({ error: "Protocol not found" }, 404);
  return c.json(row);
});

protocols.post("/", async (c) => {
  const body = await c.req.json().catch(() => null);
  if (!body) return c.json({ error: "Invalid JSON body" }, 400);

  const { address, name, alert_threshold, breaker_threshold } = body;

  if (!address || !name) {
    return c.json({ error: "address and name are required" }, 400);
  }

  if (getProtocol(address)) {
    return c.json({ error: "Protocol already registered" }, 409);
  }

  const row = insertProtocol(address, name, alert_threshold ?? 10, breaker_threshold ?? 20);
  return c.json(row, 201);
});

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
