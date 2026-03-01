import { useMemo } from "react";
import { useAccount, useConnect, useDisconnect, useSwitchChain } from "wagmi";
import { base, baseSepolia } from "wagmi/chains";

const SUPPORTED_CHAIN_IDS: readonly number[] = [base.id, baseSepolia.id] as const;

function truncateAddress(address: string): string {
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

function avatarSeed(address: string): string {
  return address.slice(2, 10);
}

export function useWallet() {
  const { address, isConnected, chainId } = useAccount();
  const { connect, connectAsync, connectors, isPending: isConnecting, error: connectError } = useConnect();
  const { disconnect } = useDisconnect();
  const { switchChain, isPending: isSwitching } = useSwitchChain();

  const isWrongNetwork = Boolean(chainId && !(SUPPORTED_CHAIN_IDS as readonly number[]).includes(chainId));

  const state = useMemo(
    () => ({
      address,
      isConnected,
      chainId,
      shortAddress: address ? truncateAddress(address) : "",
      avatar: address ? avatarSeed(address) : "",
      isWrongNetwork,
      isConnecting,
      isSwitching,
      connectError,
      connectors,
      connect,
      connectAsync,
      disconnect,
      switchChain,
    }),
    [
      address,
      chainId,
      connect,
      connectAsync,
      connectError,
      connectors,
      disconnect,
      isConnected,
      isConnecting,
      isSwitching,
      isWrongNetwork,
      switchChain,
    ]
  );

  return state;
}

export { SUPPORTED_CHAIN_IDS };
