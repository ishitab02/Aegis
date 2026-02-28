/**
 * x402 Payment Middleware for Hono.
 *
 * Implements HTTP 402 Payment Required flow:
 * 1. Client sends request without payment
 * 2. Server responds 402 with payment requirements
 * 3. Client pays via x402 facilitator
 * 4. Client retries with X-402-Payment header
 * 5. Server verifies payment and processes request
 *
 * For the hackathon demo, this middleware checks for the
 * X-402-Payment header. In production it would verify the
 * payment receipt via the x402 facilitator.
 */

import type { Context, Next } from "hono";
import { config } from "../config.js";

type PriceConfig = {
  price: string;
  description: string;
};

const PAYMENT_ROUTES: Record<string, PriceConfig> = {
  "POST /api/v1/forensics": {
    price: "$1.00",
    description: "AEGIS forensic analysis report",
  },
  "GET /api/v1/reports/:id/full": {
    price: "$0.50",
    description: "Full threat report with details",
  },
};

export async function x402PaymentMiddleware(c: Context, next: Next) {
  const routeKey = `${c.req.method} ${c.req.routePath}`;
  const priceConfig = PAYMENT_ROUTES[routeKey];

  if (!priceConfig) {
    return next();
  }

  const paymentHeader = c.req.header("X-402-Payment");

  if (!paymentHeader) {
    return c.json(
      {
        error: "Payment Required",
        x402: {
          version: 1,
          price: priceConfig.price,
          currency: "USDC",
          network: "base-sepolia",
          facilitatorUrl: config.x402FacilitatorUrl,
          payeeAddress: config.payeeAddress,
          description: priceConfig.description,
        },
      },
      402
    );
  }

  // In production: verify payment receipt via facilitator
  // For demo: accept any non-empty payment header
  return next();
}
