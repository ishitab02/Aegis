import { cors } from "hono/cors";

export const corsMiddleware = cors({
  origin: ["http://localhost:5173", "http://localhost:3000"],
  allowMethods: ["GET", "POST", "OPTIONS"],
  allowHeaders: ["Content-Type", "Authorization", "X-402-Payment"],
  maxAge: 86400,
});
