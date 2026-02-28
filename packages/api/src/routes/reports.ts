import { Hono } from "hono";
import {
  getCircuitBreakerState,
  getProtocolReports,
  getProtocolTVL,
  isProtocolPaused,
} from "../services/contractReader.js";
import { config } from "../config.js";

const reports = new Hono();

// GET /protocol — protocol status (on-chain reads)
reports.get("/protocol", async (c) => {
  const protocol = c.req.query("address") || config.protocolToMonitor;
  if (!protocol) {
    return c.json({ error: "address query param required" }, 400);
  }

  const [paused, tvl, breakerState, reportIds] = await Promise.all([
    isProtocolPaused(protocol),
    getProtocolTVL(protocol),
    getCircuitBreakerState(protocol),
    getProtocolReports(protocol, 5),
  ]);

  return c.json({
    address: protocol,
    paused,
    tvl,
    circuitBreaker: breakerState,
    recentReports: reportIds,
    timestamp: Math.floor(Date.now() / 1000),
  });
});

// GET /reports — on-chain threat reports for protocol
reports.get("/", async (c) => {
  const protocol = c.req.query("address") || config.protocolToMonitor;
  const limit = parseInt(c.req.query("limit") ?? "10", 10);

  if (!protocol) {
    return c.json({ error: "address query param required" }, 400);
  }

  const reportIds = await getProtocolReports(protocol, limit);
  return c.json({ protocol, reports: reportIds });
});

export { reports };
