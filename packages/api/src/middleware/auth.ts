// api key auth. disabled when API_KEYS env is unset (open access).

import type { Context, Next } from "hono";

const PUBLIC_PATHS = new Set([
  "/",
  "/api/v1/health",
  "/api/v1/sentinel/aggregate",
  "/api/v1/ws",
  "/api/v1/docs",
  "/api/v1/openapi",
  "/api/v1/demo/scenarios",
  "/api/v1/demo/euler-replay",
]);

let _validKeys: Set<string> | null = null;

function getValidKeys(): Set<string> {
  if (_validKeys) return _validKeys;
  const raw = process.env.API_KEYS ?? "";
  _validKeys = new Set(
    raw
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean),
  );
  return _validKeys;
}

export async function authMiddleware(c: Context, next: Next) {
  const keys = getValidKeys();

  // if no keys configured, auth is disabled (dev mode)
  if (keys.size === 0) return next();

  const pathname = new URL(c.req.url).pathname;
  if (PUBLIC_PATHS.has(pathname)) return next();

  // allow demo routes without auth
  if (pathname.startsWith("/api/v1/demo/")) return next();

  const apiKey = c.req.header("X-API-Key");
  if (!apiKey || !keys.has(apiKey)) {
    return c.json({ error: "Invalid API key" }, 401);
  }

  return next();
}
