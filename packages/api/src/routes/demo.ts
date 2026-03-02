import { Hono } from "hono";
import {
  getDemoScenarios,
  startEulerReplay,
  getEulerReplayStep,
} from "../services/agentProxy.js";

const demo = new Hono();

// GET /scenarios — list available demo scenarios
demo.get("/scenarios", async (c) => {
  const data = await getDemoScenarios();
  return c.json(data);
});

// POST /euler-replay — start Euler exploit replay
demo.post("/euler-replay", async (c) => {
  const data = await startEulerReplay();
  return c.json(data);
});

// GET /euler-replay/step/:n — get specific step
demo.get("/euler-replay/step/:n", async (c) => {
  const stepNumber = parseInt(c.req.param("n"), 10);
  if (isNaN(stepNumber) || stepNumber < 1) {
    return c.json({ error: "Invalid step number" }, 400);
  }
  const data = await getEulerReplayStep(stepNumber);
  if (!data) {
    return c.json({ error: "Step not found" }, 404);
  }
  return c.json(data);
});

export { demo };
