import { cors } from "hono/cors";

export const corsMiddleware = cors({
  origin: ["http://localhost:5173", "http://localhost:3000", "https://aegis-frontend-two.vercel.app"],
  allowMethods: ["GET", "POST", "PATCH", "OPTIONS"],
  allowHeaders: ["Content-Type", "Authorization", "X-402-Payment", "X-API-Key"],
  maxAge: 86400,
});
