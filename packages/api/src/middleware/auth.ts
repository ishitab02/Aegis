/**
 * API Key authentication middleware.
 *
 * Reads a comma-separated list of valid keys from the API_KEYS env
 * variable.  If API_KEYS is empty / unset, authentication is disabled
 * (open access) so development stays frictionless.
 *
 * Public routes (health, sentinel aggregate) are always exempt.
 */

import type { Context, Next } from "hono";

const PUBLIC_PATHS = new Set([
  "/",
  "/api/v1/health",
  "/api/v1/sentinel/aggregate",
  "/api/v1/ws",
  "/api/v1/docs",
  "/api/v1/openapi",
]);

let _validKeys: Set<string> | null = null;

function getValidKeys(): Set<string> {
  if (_validKeys) return _validKeys;
  const raw = process.env.API_KEYS ?? "";
  _validKeys = new Set(
    raw
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean)
  );
  return _validKeys;
}

export async function authMiddleware(c: Context, next: Next) {
  const keys = getValidKeys();

  // If no keys are configured, auth is disabled (dev mode)
  if (keys.size === 0) return next();

  // Always allow public routes
  const pathname = new URL(c.req.url).pathname;
  if (PUBLIC_PATHS.has(pathname)) return next();

  const apiKey = c.req.header("X-API-Key");
  if (!apiKey || !keys.has(apiKey)) {
    return c.json({ error: "Invalid API key" }, 401);
  }

  return next();
}
