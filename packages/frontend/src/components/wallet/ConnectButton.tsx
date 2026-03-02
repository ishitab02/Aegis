import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, LoaderCircle } from "lucide-react";
import { base } from "wagmi/chains";
import { AccountMenu } from "./AccountMenu";
import { useWallet } from "../../hooks/useWallet";

function avatarColor(address: string): string {
  const hash = Array.from(address.slice(2, 10)).reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return `hsl(${hash % 360} 55% 50%)`;
}

export function ConnectButton() {
  const {
    address,
    shortAddress,
    chainId,
    isConnected,
    isConnecting,
    isWrongNetwork,
    isSwitching,
    connectors,
    connect,
    disconnect,
    switchChain,
    connectError,
  } = useWallet();

  const [isConnectMenuOpen, setIsConnectMenuOpen] = useState(false);
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  const availableConnectors = useMemo(
    () =>
      connectors.map((connector) => ({
        connector,
        isReady: (connector as { ready?: boolean }).ready ?? true,
      })),
    [connectors],
  );

  useEffect(() => {
    function handleOutsideClick(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setIsConnectMenuOpen(false);
        setIsAccountMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  if (isWrongNetwork) {
    return (
      <button
        type="button"
        className="rounded-lg border border-[#7f1d1d] bg-[#7f1d1d]/30 px-3 py-2 text-sm font-medium text-[#fca5a5] transition hover:bg-[#7f1d1d]/45"
        onClick={() => switchChain({ chainId: base.id })}
        disabled={isSwitching}
      >
        {isSwitching ? "Switching..." : "Switch to Base"}
      </button>
    );
  }

  if (!isConnected || !address) {
    return (
      <div className="relative" ref={menuRef}>
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-lg border border-[var(--border-subtle)] bg-transparent px-3 py-2 text-sm font-medium text-[var(--text-primary)] transition hover:border-[var(--border-muted)] hover:bg-white/[0.02]"
          onClick={() => setIsConnectMenuOpen((open) => !open)}
          disabled={isConnecting}
        >
          {isConnecting && (
            <LoaderCircle className="h-4 w-4 animate-spin text-[var(--text-secondary)]" />
          )}
          {isConnecting ? "Connecting" : "Connect Wallet"}
        </button>

        {isConnectMenuOpen && (
          <div className="absolute right-0 top-[calc(100%+8px)] z-50 w-56 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-overlay)] p-2 shadow-2xl">
            {availableConnectors.map(({ connector, isReady }) => (
              <button
                key={connector.uid}
                type="button"
                className="mb-1 flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm text-[var(--text-secondary)] transition hover:bg-white/[0.02] hover:text-[var(--text-primary)] disabled:cursor-not-allowed disabled:opacity-50"
                disabled={!isReady || isConnecting}
                onClick={() => {
                  connect({ connector });
                  setIsConnectMenuOpen(false);
                }}
              >
                <span>{connector.name}</span>
                {!isReady && (
                  <span className="text-2xs text-[var(--text-muted)]">Not available</span>
                )}
              </button>
            ))}
            {availableConnectors.length === 0 && (
              <p className="px-3 py-2 text-xs text-[var(--text-muted)]">
                No wallet connector configured.
              </p>
            )}
            {connectError && (
              <p className="px-3 py-2 text-xs text-[#fca5a5]">{connectError.message}</p>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        className="inline-flex items-center gap-2 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3 py-2 text-sm font-medium text-[var(--text-primary)] transition hover:border-[var(--border-muted)]"
        onClick={() => setIsAccountMenuOpen((open) => !open)}
      >
        <span
          className="h-5 w-5 rounded-full"
          style={{ backgroundColor: avatarColor(address) }}
          aria-hidden
        />
        <span>{shortAddress}</span>
        <ChevronDown className="h-4 w-4 text-[var(--text-muted)]" />
      </button>

      {isAccountMenuOpen && (
        <AccountMenu
          address={address}
          chainId={chainId}
          onDisconnect={() => {
            disconnect();
            setIsAccountMenuOpen(false);
          }}
        />
      )}
    </div>
  );
}
