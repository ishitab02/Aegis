/**
 * OpenAPI specification + Swagger UI for the AEGIS API.
 *
 * Serves:
 *   GET /docs     — Swagger UI
 *   GET /openapi  — raw OpenAPI 3.1 JSON
 */

import { Hono } from "hono";
import { swaggerUI } from "@hono/swagger-ui";

const docs = new Hono();

// ---- OpenAPI 3.1 spec (hand-written, kept in sync with routes) ----

const openApiSpec = {
  openapi: "3.1.0",
  info: {
    title: "AEGIS Protocol API",
    version: "1.2.0",
    description:
      "AI-Enhanced Guardian Intelligence System — REST API for DeFi security monitoring, threat detection, and forensic analysis.",
    contact: { name: "AEGIS Team" },
  },
  servers: [{ url: "http://localhost:3000", description: "Local development" }],
  paths: {
    "/api/v1/health": {
      get: {
        tags: ["Health"],
        summary: "System health check",
        responses: {
          "200": {
            description: "Health status",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    status: { type: "string", enum: ["HEALTHY", "DEGRADED"] },
                    services: { type: "object" },
                    timestamp: { type: "integer" },
                  },
                },
              },
            },
          },
        },
      },
    },
    "/api/v1/sentinel/aggregate": {
      get: {
        tags: ["Sentinels"],
        summary: "All sentinel assessments + consensus",
        responses: {
          "200": { description: "Aggregated sentinel data" },
        },
      },
    },
    "/api/v1/sentinel/{id}": {
      get: {
        tags: ["Sentinels"],
        summary: "Single sentinel status",
        parameters: [
          {
            name: "id",
            in: "path",
            required: true,
            schema: { type: "string" },
          },
        ],
        responses: {
          "200": { description: "Sentinel details" },
          "404": { description: "Sentinel not found" },
        },
      },
    },
    "/api/v1/sentinel/detect": {
      post: {
        tags: ["Sentinels"],
        summary: "Trigger full detection cycle",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  protocol_address: { type: "string" },
                  protocol_name: { type: "string" },
                  simulate_tvl_drop_percent: { type: "number" },
                  simulate_price_deviation_percent: { type: "number" },
                  simulate_short_voting_period: { type: "boolean" },
                },
                required: ["protocol_address"],
              },
            },
          },
        },
        responses: {
          "200": { description: "Detection result" },
          "400": { description: "Missing protocol_address" },
        },
      },
    },
    "/api/v1/alerts": {
      get: {
        tags: ["Alerts"],
        summary: "Paginated list of alerts",
        parameters: [
          {
            name: "page",
            in: "query",
            schema: { type: "integer", default: 1 },
          },
          {
            name: "limit",
            in: "query",
            schema: { type: "integer", default: 20 },
          },
          { name: "protocol", in: "query", schema: { type: "string" } },
        ],
        responses: {
          "200": {
            description: "Alert list",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    items: { type: "array", items: { $ref: "#/components/schemas/Alert" } },
                    total: { type: "integer" },
                    page: { type: "integer" },
                    limit: { type: "integer" },
                  },
                },
              },
            },
          },
        },
      },
      post: {
        tags: ["Alerts"],
        summary: "Create a new alert",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  protocol: { type: "string" },
                  threat_level: {
                    type: "string",
                    enum: ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
                  },
                  confidence: { type: "number" },
                  action: { type: "string" },
                  consensus_data: { type: "object", nullable: true },
                },
                required: ["protocol", "threat_level", "confidence", "action"],
              },
            },
          },
        },
        responses: {
          "201": { description: "Alert created" },
          "400": { description: "Missing required fields" },
        },
      },
    },
    "/api/v1/alerts/{id}": {
      get: {
        tags: ["Alerts"],
        summary: "Get a single alert by ID",
        parameters: [
          {
            name: "id",
            in: "path",
            required: true,
            schema: { type: "string" },
          },
        ],
        responses: {
          "200": { description: "Alert details" },
          "404": { description: "Alert not found" },
        },
      },
    },
    "/api/v1/protocols": {
      get: {
        tags: ["Protocols"],
        summary: "List registered protocols",
        parameters: [
          { name: "active", in: "query", schema: { type: "string", enum: ["true", "false"] } },
        ],
        responses: {
          "200": { description: "Protocol list" },
        },
      },
      post: {
        tags: ["Protocols"],
        summary: "Register a new protocol",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  address: { type: "string" },
                  name: { type: "string" },
                  alert_threshold: { type: "number", default: 10 },
                  breaker_threshold: { type: "number", default: 20 },
                },
                required: ["address", "name"],
              },
            },
          },
        },
        responses: {
          "201": { description: "Protocol registered" },
          "400": { description: "Missing required fields" },
          "409": { description: "Protocol already registered" },
        },
      },
    },
    "/api/v1/protocols/{address}": {
      get: {
        tags: ["Protocols"],
        summary: "Get protocol details",
        parameters: [
          {
            name: "address",
            in: "path",
            required: true,
            schema: { type: "string" },
          },
        ],
        responses: {
          "200": { description: "Protocol details" },
          "404": { description: "Protocol not found" },
        },
      },
      patch: {
        tags: ["Protocols"],
        summary: "Update protocol thresholds / name",
        parameters: [
          {
            name: "address",
            in: "path",
            required: true,
            schema: { type: "string" },
          },
        ],
        requestBody: {
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  name: { type: "string" },
                  alert_threshold: { type: "number" },
                  breaker_threshold: { type: "number" },
                  active: { type: "integer", enum: [0, 1] },
                },
              },
            },
          },
        },
        responses: {
          "200": { description: "Updated protocol" },
          "404": { description: "Protocol not found" },
        },
      },
    },
    "/api/v1/protocols/{address}/status": {
      get: {
        tags: ["Protocols"],
        summary: "Live circuit breaker status (on-chain read)",
        parameters: [
          {
            name: "address",
            in: "path",
            required: true,
            schema: { type: "string" },
          },
        ],
        responses: {
          "200": { description: "Circuit breaker state" },
        },
      },
    },
    "/api/v1/forensics": {
      get: {
        tags: ["Forensics"],
        summary: "List forensic reports",
        responses: { "200": { description: "Report list" } },
      },
      post: {
        tags: ["Forensics"],
        summary: "Run forensic analysis (x402 payment gated)",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  tx_hash: { type: "string" },
                  protocol: { type: "string" },
                  description: { type: "string" },
                },
                required: ["tx_hash", "protocol"],
              },
            },
          },
        },
        responses: {
          "200": { description: "Forensic report" },
          "400": { description: "Missing required fields" },
          "402": { description: "Payment required" },
        },
      },
    },
    "/api/v1/forensics/{id}": {
      get: {
        tags: ["Forensics"],
        summary: "Get forensic report by ID",
        parameters: [
          {
            name: "id",
            in: "path",
            required: true,
            schema: { type: "string" },
          },
        ],
        responses: {
          "200": { description: "Report details" },
          "404": { description: "Report not found" },
        },
      },
    },
    "/api/v1/ws": {
      get: {
        tags: ["WebSocket"],
        summary: "Server-Sent Events stream for real-time alerts",
        description:
          "Connect with EventSource to receive live alert notifications. Events: `alert` (new alert), `system` (connection info), `ping` (heartbeat).",
        responses: {
          "200": {
            description: "SSE stream",
            content: { "text/event-stream": {} },
          },
        },
      },
    },
  },
  components: {
    schemas: {
      Alert: {
        type: "object",
        properties: {
          id: { type: "string" },
          protocol: { type: "string" },
          threat_level: {
            type: "string",
            enum: ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
          },
          confidence: { type: "number" },
          action: { type: "string" },
          consensus_data: { type: "string", nullable: true },
          created_at: { type: "integer" },
        },
      },
      Protocol: {
        type: "object",
        properties: {
          address: { type: "string" },
          name: { type: "string" },
          alert_threshold: { type: "number" },
          breaker_threshold: { type: "number" },
          active: { type: "integer" },
          registered_at: { type: "integer" },
        },
      },
    },
    securitySchemes: {
      ApiKeyAuth: {
        type: "apiKey",
        in: "header",
        name: "X-API-Key",
      },
    },
  },
  security: [{ ApiKeyAuth: [] }],
};

// ---- Routes ----

docs.get("/openapi", (c) => c.json(openApiSpec));

docs.get(
  "/docs",
  swaggerUI({
    url: "/api/v1/openapi",
  }),
);

export { docs };
