import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { logger } from "hono/logger";
import { corsMiddleware } from "./middleware/cors.js";
import { x402PaymentMiddleware } from "./middleware/x402Payment.js";
import { health } from "./routes/health.js";
import { sentinel } from "./routes/sentinel.js";
import { forensics } from "./routes/forensics.js";
import { reports } from "./routes/reports.js";
import { config } from "./config.js";

const app = new Hono();

// ---- Global Middleware ----
app.use("*", logger());
app.use("*", corsMiddleware);
app.use("*", x402PaymentMiddleware);

// ---- Root ----
app.get("/", (c) =>
  c.json({
    name: "AEGIS Protocol API",
    version: "1.0.0",
    description: "AI-Enhanced Guardian Intelligence System for DeFi Security",
    endpoints: {
      health: "/api/v1/health",
      sentinels: "/api/v1/sentinel/aggregate",
      detect: "POST /api/v1/sentinel/detect",
      forensics: "/api/v1/forensics",
      reports: "/api/v1/reports/protocol",
    },
  })
);

// ---- API Routes ----
app.route("/api/v1/health", health);
app.route("/api/v1/sentinel", sentinel);
app.route("/api/v1/forensics", forensics);
app.route("/api/v1/reports", reports);

// ---- Start Server ----
console.log(`AEGIS API starting on port ${config.port}...`);
console.log(`  Agent API: ${config.agentApiUrl}`);
console.log(`  RPC: ${config.rpcUrl}`);

serve({
  fetch: app.fetch,
  port: config.port,
});

console.log(`AEGIS API running at http://localhost:${config.port}`);

export default app;
