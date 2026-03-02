// x402 payment gate. for the hackathon demo we only check for the
// X-402-Payment header; production would verify via the facilitator.

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
      402,
    );
  }

  // in production: verify payment receipt via facilitator
  // for demo: accept any non-empty payment header
  return next();
}
