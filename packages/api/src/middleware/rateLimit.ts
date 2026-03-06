// sliding-window rate limiter keyed by client IP.
// defaults: 100 req / 60s. override via RATE_LIMIT_MAX & RATE_LIMIT_WINDOW_MS.

import type { Context, Next } from "hono";

interface WindowEntry {
  count: number;
  resetAt: number;
}

const MAX_REQUESTS = parseInt(process.env.RATE_LIMIT_MAX ?? "100", 10);
const WINDOW_MS = parseInt(process.env.RATE_LIMIT_WINDOW_MS ?? "60000", 10);

const windows = new Map<string, WindowEntry>();

// prune stale entries every 5 min to prevent unbounded growth
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
    c.req.header("x-forwarded-for")?.split(",")[0]?.trim() ?? c.req.header("x-real-ip") ?? "unknown"
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
      429,
    );
  }

  return next();
}
