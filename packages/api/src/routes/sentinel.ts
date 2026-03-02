import { Hono } from "hono";
import { randomUUID } from "node:crypto";
import { getSentinelAggregate, getSentinelById, runDetection } from "../services/agentProxy.js";
import { config } from "../config.js";
import { insertAlert } from "../db/index.js";
import { broadcast } from "./ws.js";
import { sendAlert } from "../services/telegram.js";

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

  // Auto-create alert in DB when consensus is reached with HIGH or CRITICAL
  try {
    const consensus = (result as any)?.consensus;
    if (
      consensus?.consensus_reached &&
      (consensus.final_threat_level === "CRITICAL" || consensus.final_threat_level === "HIGH")
    ) {
      const row = insertAlert({
        id: randomUUID(),
        protocol: protocolAddress,
        protocol_name: body.protocol_name || "MockProtocol",
        threat_level: consensus.final_threat_level,
        confidence: consensus.votes?.[0]?.confidence ?? 0.9,
        action: consensus.action_recommended || "ALERT",
        consensus_data: JSON.stringify(consensus),
      });
      broadcast(row);
      if (row.threat_level === "CRITICAL" || row.threat_level === "HIGH") {
        sendAlert(row).catch(() => {});
      }
    }
  } catch (e) {
    console.error("[sentinel/detect] auto-alert creation failed:", e);
  }

  return c.json(result);
});

export { sentinel };
