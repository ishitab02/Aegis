/**
 * Rate-limiting middleware.
 *
 * Uses an in-memory sliding-window counter keyed by client IP.
 * Defaults to 100 requests per 60-second window.
 *
 * Env overrides:
 *   RATE_LIMIT_MAX   — max requests per window (default 100)
 *   RATE_LIMIT_WINDOW_MS — window length in ms (default 60000)
 *
 * Returns 429 Too Many Requests when the limit is exceeded, with a
 * Retry-After header indicating how many seconds to wait.
 */

import type { Context, Next } from "hono";

interface WindowEntry {
  count: number;
  resetAt: number;
}

const MAX_REQUESTS = parseInt(process.env.RATE_LIMIT_MAX ?? "100", 10);
const WINDOW_MS = parseInt(process.env.RATE_LIMIT_WINDOW_MS ?? "60000", 10);

const windows = new Map<string, WindowEntry>();

// Prune stale entries every 5 minutes to avoid unbounded growth
setInterval(() => {
  const now = Date.now();
  for (const [key, entry] of windows) {
    if (entry.resetAt <= now) {
      windows.delete(key);
    }
  }
}, 5 * 60_000).unref();

function getClientIp(c: Context): string {
  return (
    c.req.header("x-forwarded-for")?.split(",")[0]?.trim() ??
    c.req.header("x-real-ip") ??
    "unknown"
  );
}

export async function rateLimitMiddleware(c: Context, next: Next) {
  const ip = getClientIp(c);
  const now = Date.now();

  let entry = windows.get(ip);

  if (!entry || entry.resetAt <= now) {
    entry = { count: 0, resetAt: now + WINDOW_MS };
    windows.set(ip, entry);
  }

  entry.count++;

  // Always send informational rate-limit headers
  c.header("X-RateLimit-Limit", String(MAX_REQUESTS));
  c.header("X-RateLimit-Remaining", String(Math.max(0, MAX_REQUESTS - entry.count)));
  c.header("X-RateLimit-Reset", String(Math.ceil(entry.resetAt / 1000)));

  if (entry.count > MAX_REQUESTS) {
    const retryAfter = Math.ceil((entry.resetAt - now) / 1000);
    c.header("Retry-After", String(retryAfter));
    return c.json(
      {
        error: "Too Many Requests",
        retryAfter,
      },
      429
    );
  }

  return next();
}
