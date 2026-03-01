import { Hono } from "hono";
import {
  getSentinelAggregate,
  getSentinelById,
  runDetection,
} from "../services/agentProxy.js";
import { config } from "../config.js";

const sentinel = new Hono();

// GET /aggregate — all sentinel assessments + consensus
sentinel.get("/aggregate", async (c) => {
  const data = await getSentinelAggregate();
  return c.json(data);
});

// GET /:id — single sentinel status
sentinel.get("/:id", async (c) => {
  const id = c.req.param("id");
  const data = await getSentinelById(id);
  if (!data) {
    return c.json({ error: "Sentinel not found" }, 404);
  }
  return c.json(data);
});

// POST /detect — trigger full detection cycle
sentinel.post("/detect", async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const protocolAddress = body.protocol_address || config.protocolToMonitor;

  if (!protocolAddress) {
    return c.json({ error: "protocol_address is required" }, 400);
  }

  const result = await runDetection({
    protocol_address: protocolAddress,
    protocol_name: body.protocol_name || "MockProtocol",
    simulate_tvl_drop_percent: body.simulate_tvl_drop_percent,
    simulate_price_deviation_percent: body.simulate_price_deviation_percent,
    simulate_short_voting_period: body.simulate_short_voting_period,
  });
  return c.json(result);
});

export { sentinel };
