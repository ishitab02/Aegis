import { useMemo, useState } from "react";
import { Check, Copy, ExternalLink, LogOut } from "lucide-react";

function explorerUrl(address: string, chainId?: number) {
  if (chainId === 84532) {
    return `https://sepolia.basescan.org/address/${address}`;
  }
  return `https://basescan.org/address/${address}`;
}

function avatarColor(address: string): string {
  const hash = Array.from(address.slice(2, 10)).reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return `hsl(${hash % 360} 55% 50%)`;
}

export function AccountMenu({
  address,
  chainId,
  onDisconnect,
}: {
  address: string;
  chainId?: number;
  onDisconnect: () => void;
}) {
  const [copied, setCopied] = useState(false);

  const url = useMemo(() => explorerUrl(address, chainId), [address, chainId]);

  async function copyAddress() {
    await navigator.clipboard.writeText(address);
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  }

  return (
    <div className="absolute right-0 top-[calc(100%+8px)] z-50 w-56 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-overlay)] p-2 shadow-2xl">
      <div className="mb-2 flex items-center gap-3 rounded-md border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3">
        <span
          className="inline-flex h-8 w-8 rounded-full"
          style={{ backgroundColor: avatarColor(address) }}
          aria-hidden
        />
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-[var(--text-primary)]">{`${address.slice(0, 6)}...${address.slice(-4)}`}</p>
          <p className="truncate text-xs text-[var(--text-muted)]">Connected</p>
        </div>
      </div>

      <button
        type="button"
        className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-[var(--text-secondary)] transition hover:bg-white/[0.02] hover:text-[var(--text-primary)]"
        onClick={copyAddress}
      >
        {copied ? (
          <Check className="h-4 w-4 text-[var(--success)]" />
        ) : (
          <Copy className="h-4 w-4" />
        )}
        {copied ? "Copied" : "Copy address"}
      </button>

      <a
        href={url}
        target="_blank"
        rel="noreferrer"
        className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-[var(--text-secondary)] transition hover:bg-white/[0.02] hover:text-[var(--text-primary)]"
      >
        <ExternalLink className="h-4 w-4" />
        View on explorer
      </a>

      <button
        type="button"
        className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-[#fca5a5] transition hover:bg-[#7f1d1d]/30"
        onClick={onDisconnect}
      >
        <LogOut className="h-4 w-4" />
        Disconnect
      </button>
    </div>
  );
}
