import { cors } from "hono/cors";

<<<<<<< HEAD
const allowedOrigins = [
  "http://localhost:5173",
  "http://localhost:3000",
=======
// Build allowed origins from environment + defaults
const allowedOrigins = [
  "http://localhost:5173",
  "http://localhost:3000",
  // Add production origins from env (comma-separated)
>>>>>>> d16fae7 (much changes)
  ...(process.env.CORS_ORIGINS?.split(",").map((o) => o.trim()) || []),
].filter(Boolean);

export const corsMiddleware = cors({
  origin: allowedOrigins,
  allowMethods: ["GET", "POST", "PATCH", "OPTIONS"],
  allowHeaders: ["Content-Type", "Authorization", "X-402-Payment", "X-API-Key"],
  maxAge: 86400,
});
