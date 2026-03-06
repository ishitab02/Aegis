import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { logger } from "hono/logger";
import { corsMiddleware } from "./middleware/cors.js";
import { rateLimitMiddleware } from "./middleware/rateLimit.js";
import { authMiddleware } from "./middleware/auth.js";
import { x402PaymentMiddleware } from "./middleware/x402Payment.js";
import { health } from "./routes/health.js";
import { sentinel } from "./routes/sentinel.js";
import { forensics } from "./routes/forensics.js";
import { reports } from "./routes/reports.js";
import { alerts } from "./routes/alerts.js";
import { protocols } from "./routes/protocols.js";
import { ws, subscriberCount } from "./routes/ws.js";
import { docs } from "./routes/docs.js";
import { demo } from "./routes/demo.js";
import { config } from "./config.js";
import { getDb } from "./db/index.js";

const app = new Hono();

getDb();
console.log("[db] SQLite database initialised");

app.use("*", logger());
app.use("*", corsMiddleware);
app.use("*", rateLimitMiddleware);
app.use("*", authMiddleware);
app.use("*", x402PaymentMiddleware);

app.get("/", (c) =>
  c.json({
    name: "AEGIS Protocol API",
    version: "1.3.0",
    description: "AI-Enhanced Guardian Intelligence System for DeFi Security",
    endpoints: {
      health: "/api/v1/health",
      sentinels: "/api/v1/sentinel/aggregate",
      detect: "POST /api/v1/sentinel/detect",
      forensics: "/api/v1/forensics",
      reports: "/api/v1/reports/protocol",
      alerts: "/api/v1/alerts",
      protocols: "/api/v1/protocols",
      demo: "/api/v1/demo/scenarios",
      ws: "/api/v1/ws (SSE)",
      docs: "/api/v1/docs",
    },
  }),
);

app.route("/api/v1/health", health);
app.route("/api/v1/sentinel", sentinel);
app.route("/api/v1/forensics", forensics);
app.route("/api/v1/reports", reports);
app.route("/api/v1/alerts", alerts);
app.route("/api/v1/protocols", protocols);
app.route("/api/v1/ws", ws);
app.route("/api/v1/demo", demo);
app.route("/api/v1", docs);

console.log(`AEGIS API starting on port ${config.port}...`);
console.log(`  Agent API: ${config.agentApiUrl}`);
console.log(`  RPC: ${config.rpcUrl}`);

serve({
  fetch: app.fetch,
  port: config.port,
});

console.log(`AEGIS API running at http://localhost:${config.port}`);

export default app;
