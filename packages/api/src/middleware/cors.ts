import { cors } from "hono/cors";

const allowedOrigins = [
  "http://localhost:5173",
  "http://localhost:3000",
  ...(process.env.CORS_ORIGINS?.split(",").map((o) => o.trim()) || []),
].filter(Boolean);

export const corsMiddleware = cors({
  origin: allowedOrigins,
  allowMethods: ["GET", "POST", "PATCH", "OPTIONS"],
  allowHeaders: ["Content-Type", "Authorization", "X-402-Payment", "X-API-Key"],
  maxAge: 86400,
});
