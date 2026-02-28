import { Hono } from "hono";
import { getAgentHealth } from "../services/agentProxy.js";
import { getActiveSentinels } from "../services/contractReader.js";

const health = new Hono();

health.get("/", async (c) => {
  const [agentHealth, sentinels] = await Promise.all([
    getAgentHealth(),
    getActiveSentinels(),
  ]);

  const status =
    agentHealth.status === "HEALTHY" ? "HEALTHY" : "DEGRADED";

  return c.json({
    status,
    services: {
      agentApi: agentHealth,
      onChain: {
        activeSentinels: sentinels.length,
      },
    },
    timestamp: Math.floor(Date.now() / 1000),
  });
});

export { health };
