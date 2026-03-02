import { Hono } from "hono";
import { insertAlert, getAlert, listAlerts } from "../db/index.js";
import { randomUUID } from "node:crypto";
import { sendAlert } from "../services/telegram.js";
import { broadcast } from "./ws.js";

const alerts = new Hono();

alerts.get("/", (c) => {
  const page = Math.max(1, parseInt(c.req.query("page") ?? "1", 10));
  const limit = Math.min(100, Math.max(1, parseInt(c.req.query("limit") ?? "20", 10)));
  const protocol = c.req.query("protocol");

  const result = listAlerts(page, limit, protocol);
  return c.json(result);
});

alerts.get("/:id", (c) => {
  const row = getAlert(c.req.param("id"));
  if (!row) return c.json({ error: "Alert not found" }, 404);
  return c.json(row);
});

alerts.post("/", async (c) => {
  const body = await c.req.json().catch(() => null);
  if (!body) return c.json({ error: "Invalid JSON body" }, 400);

  const { protocol, protocol_name, threat_level, confidence, action, consensus_data } = body;

  if (!protocol || !threat_level || confidence === undefined || !action) {
    return c.json({ error: "protocol, threat_level, confidence, and action are required" }, 400);
  }

  const id = body.id ?? randomUUID();

  const row = insertAlert({
    id,
    protocol,
    protocol_name: protocol_name || "",
    threat_level,
    confidence: Number(confidence),
    action,
    consensus_data: consensus_data ? JSON.stringify(consensus_data) : null,
  });

  broadcast(row);

  // telegram notification for HIGH/CRITICAL (fire-and-forget)
  if (threat_level === "CRITICAL" || threat_level === "HIGH") {
    sendAlert(row).catch(() => {
      /* swallow – notifications are best-effort */
    });
  }

  return c.json(row, 201);
});

export { alerts };
