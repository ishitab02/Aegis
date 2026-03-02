/**
 * Telegram notification service.
 *
 * Sends formatted alert messages to a Telegram chat when HIGH or
 * CRITICAL threats are detected.
 *
 * Required env variables:
 *   TELEGRAM_BOT_TOKEN  — Bot API token from BotFather
 *   TELEGRAM_CHAT_ID    — Chat / channel / group ID to post to
 *
 * If either env var is missing the service degrades silently (logs a
 * warning once and becomes a no-op).
 */

import type { AlertRow } from "../db/index.js";

const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN ?? "";
const CHAT_ID = process.env.TELEGRAM_CHAT_ID ?? "";

let _warned = false;

function isConfigured(): boolean {
  if (BOT_TOKEN && CHAT_ID) return true;
  if (!_warned) {
    console.warn(
      "[telegram] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set – notifications disabled"
    );
    _warned = true;
  }
  return false;
}

/**
 * Re-export a minimal interface so the rest of the app doesn't depend
 * on the node-telegram-bot-api types.
 */
async function sendMessage(text: string): Promise<void> {
  if (!isConfigured()) return;

  const url = `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: CHAT_ID,
      text,
      parse_mode: "Markdown",
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    console.error(`[telegram] sendMessage failed (${res.status}): ${body}`);
  }
}

const THREAT_EMOJI: Record<string, string> = {
  CRITICAL: "🚨",
  HIGH: "⚠️",
  MEDIUM: "🔶",
  LOW: "🔵",
  NONE: "✅",
};

/** Send a formatted alert notification to Telegram. */
export async function sendAlert(alert: AlertRow): Promise<void> {
  const emoji = THREAT_EMOJI[alert.threat_level] ?? "❓";
  const confidence = (alert.confidence * 100).toFixed(1);
  const time = new Date(alert.created_at * 1000).toISOString();

  const proto = alert.protocol_name || alert.protocol;
  const text = [
    `${emoji} *${alert.threat_level} ALERT*`,
    "",
    `*Protocol:* ${proto}`,
    `*Address:* \`${alert.protocol}\``,
    `*Threat Level:* ${alert.threat_level}`,
    `*Confidence:* ${confidence}%`,
    `*Action:* ${alert.action}`,
    `*Time:* ${time}`,
    "",
    `_AEGIS Protocol — AI-Enhanced Guardian Intelligence System_`,
  ].join("\n");

  await sendMessage(text);
}

/** Send a plain text message (for health/status pings). */
export async function sendText(text: string): Promise<void> {
  await sendMessage(text);
}
