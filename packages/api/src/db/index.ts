import Database from "better-sqlite3";
import path from "node:path";
import fs from "node:fs";

const DB_PATH = process.env.DATABASE_PATH ?? "./data/aegis.db";

let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (_db) return _db;

  const dir = path.dirname(DB_PATH);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  _db = new Database(DB_PATH);
  _db.pragma("journal_mode = WAL");
  _db.pragma("foreign_keys = ON");

  migrate(_db);
  return _db;
}

function migrate(db: Database.Database): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS alerts (
      id          TEXT PRIMARY KEY,
      protocol    TEXT NOT NULL,
      protocol_name TEXT DEFAULT '',
      threat_level TEXT NOT NULL,
      confidence  REAL NOT NULL,
      action      TEXT NOT NULL,
      consensus_data TEXT,
      created_at  INTEGER DEFAULT (unixepoch())
    );

    CREATE TABLE IF NOT EXISTS protocols (
      address            TEXT PRIMARY KEY,
      name               TEXT NOT NULL,
      alert_threshold    REAL DEFAULT 10,
      breaker_threshold  REAL DEFAULT 20,
      active             INTEGER DEFAULT 1,
      registered_at      INTEGER DEFAULT (unixepoch())
    );

    CREATE TABLE IF NOT EXISTS forensic_reports (
      id          TEXT PRIMARY KEY,
      protocol    TEXT NOT NULL,
      tx_hash     TEXT,
      report      TEXT,
      created_at  INTEGER DEFAULT (unixepoch())
    );

    CREATE INDEX IF NOT EXISTS idx_alerts_protocol    ON alerts(protocol);
    CREATE INDEX IF NOT EXISTS idx_alerts_created_at   ON alerts(created_at);
    CREATE INDEX IF NOT EXISTS idx_forensic_protocol   ON forensic_reports(protocol);
  `);

  // add column if missing (migration for existing dbs)
  const cols = db.prepare("PRAGMA table_info(alerts)").all() as Array<{ name: string }>;
  if (!cols.some((c) => c.name === "protocol_name")) {
    db.exec("ALTER TABLE alerts ADD COLUMN protocol_name TEXT DEFAULT ''");
  }
}

export interface AlertRow {
  id: string;
  protocol: string;
  protocol_name: string;
  threat_level: string;
  confidence: number;
  action: string;
  consensus_data: string | null;
  created_at: number;
}

export function insertAlert(alert: Omit<AlertRow, "created_at">): AlertRow {
  const db = getDb();
  const stmt = db.prepare(`
    INSERT INTO alerts (id, protocol, protocol_name, threat_level, confidence, action, consensus_data)
    VALUES (@id, @protocol, @protocol_name, @threat_level, @confidence, @action, @consensus_data)
  `);
  stmt.run({
    ...alert,
    protocol_name: alert.protocol_name || lookupProtocolName(db, alert.protocol),
  });
  return db.prepare("SELECT * FROM alerts WHERE id = ?").get(alert.id) as AlertRow;
}

function lookupProtocolName(db: Database.Database, address: string): string {
  const row = db.prepare("SELECT name FROM protocols WHERE address = ?").get(address) as
    | { name: string }
    | undefined;
  return row?.name || address;
}

export function getAlert(id: string): AlertRow | undefined {
  const db = getDb();
  const row = db.prepare("SELECT * FROM alerts WHERE id = ?").get(id) as AlertRow | undefined;
  if (row && !row.protocol_name) {
    row.protocol_name = lookupProtocolName(db, row.protocol);
  }
  return row;
}

export function listAlerts(
  page = 1,
  limit = 20,
  protocol?: string,
): { items: AlertRow[]; total: number; page: number; limit: number } {
  const db = getDb();
  const offset = (page - 1) * limit;

  const where = protocol ? "WHERE protocol = ?" : "";
  const params = protocol ? [protocol] : [];

  const total = (
    db.prepare(`SELECT COUNT(*) AS cnt FROM alerts ${where}`).get(...params) as {
      cnt: number;
    }
  ).cnt;

  const items = db
    .prepare(`SELECT * FROM alerts ${where} ORDER BY created_at DESC LIMIT ? OFFSET ?`)
    .all(...params, limit, offset) as AlertRow[];

  // enrich legacy rows missing protocol_name
  for (const item of items) {
    if (!item.protocol_name) {
      item.protocol_name = lookupProtocolName(db, item.protocol);
    }
  }

  return { items, total, page, limit };
}

export interface ProtocolRow {
  address: string;
  name: string;
  alert_threshold: number;
  breaker_threshold: number;
  active: number;
  registered_at: number;
}

export function insertProtocol(
  address: string,
  name: string,
  alertThreshold = 10,
  breakerThreshold = 20,
): ProtocolRow {
  const db = getDb();
  db.prepare(
    `INSERT INTO protocols (address, name, alert_threshold, breaker_threshold)
     VALUES (?, ?, ?, ?)`,
  ).run(address, name, alertThreshold, breakerThreshold);
  return db.prepare("SELECT * FROM protocols WHERE address = ?").get(address) as ProtocolRow;
}

export function getProtocol(address: string): ProtocolRow | undefined {
  return getDb().prepare("SELECT * FROM protocols WHERE address = ?").get(address) as
    | ProtocolRow
    | undefined;
}

export function listProtocols(activeOnly = false): ProtocolRow[] {
  const db = getDb();
  if (activeOnly) {
    return db
      .prepare("SELECT * FROM protocols WHERE active = 1 ORDER BY registered_at DESC")
      .all() as ProtocolRow[];
  }
  return db.prepare("SELECT * FROM protocols ORDER BY registered_at DESC").all() as ProtocolRow[];
}

export function updateProtocol(
  address: string,
  updates: { name?: string; alert_threshold?: number; breaker_threshold?: number; active?: number },
): ProtocolRow | undefined {
  const db = getDb();
  const fields: string[] = [];
  const values: unknown[] = [];

  if (updates.name !== undefined) {
    fields.push("name = ?");
    values.push(updates.name);
  }
  if (updates.alert_threshold !== undefined) {
    fields.push("alert_threshold = ?");
    values.push(updates.alert_threshold);
  }
  if (updates.breaker_threshold !== undefined) {
    fields.push("breaker_threshold = ?");
    values.push(updates.breaker_threshold);
  }
  if (updates.active !== undefined) {
    fields.push("active = ?");
    values.push(updates.active);
  }

  if (fields.length === 0) return getProtocol(address);

  values.push(address);
  db.prepare(`UPDATE protocols SET ${fields.join(", ")} WHERE address = ?`).run(...values);
  return getProtocol(address);
}

export interface ForensicReportRow {
  id: string;
  protocol: string;
  tx_hash: string | null;
  report: string | null;
  created_at: number;
}

export function insertForensicReport(
  id: string,
  protocol: string,
  txHash: string | null,
  report: string | null,
): ForensicReportRow {
  const db = getDb();
  db.prepare(
    `INSERT INTO forensic_reports (id, protocol, tx_hash, report)
     VALUES (?, ?, ?, ?)`,
  ).run(id, protocol, txHash, report);
  return db.prepare("SELECT * FROM forensic_reports WHERE id = ?").get(id) as ForensicReportRow;
}

export function getForensicReportRow(id: string): ForensicReportRow | undefined {
  return getDb().prepare("SELECT * FROM forensic_reports WHERE id = ?").get(id) as
    | ForensicReportRow
    | undefined;
}

export function listForensicReportRows(
  page = 1,
  limit = 20,
): { items: ForensicReportRow[]; total: number; page: number; limit: number } {
  const db = getDb();
  const offset = (page - 1) * limit;
  const total = (
    db.prepare("SELECT COUNT(*) AS cnt FROM forensic_reports").get() as { cnt: number }
  ).cnt;
  const items = db
    .prepare("SELECT * FROM forensic_reports ORDER BY created_at DESC LIMIT ? OFFSET ?")
    .all(limit, offset) as ForensicReportRow[];
  return { items, total, page, limit };
}
