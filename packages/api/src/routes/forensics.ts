import { Hono } from "hono";
import {
  runForensics,
  getForensicReport,
  listForensicReports,
} from "../services/agentProxy.js";

const forensics = new Hono();

// POST / — run forensic analysis (x402 payment gated)
forensics.post("/", async (c) => {
  const body = await c.req.json();
  const { tx_hash, protocol, description } = body;

  if (!tx_hash || !protocol) {
    return c.json(
      { error: "tx_hash and protocol are required" },
      400
    );
  }

  const report = await runForensics(tx_hash, protocol, description);
  return c.json(report);
});

// GET / — list all forensic reports
forensics.get("/", async (c) => {
  const reports = await listForensicReports();
  return c.json(reports);
});

// GET /:id — get specific forensic report
forensics.get("/:id", async (c) => {
  const id = c.req.param("id");
  const report = await getForensicReport(id);
  if (!report) {
    return c.json({ error: "Report not found" }, 404);
  }
  return c.json(report);
});

export { forensics };
