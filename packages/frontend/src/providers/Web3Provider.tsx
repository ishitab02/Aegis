import type { ReactNode } from "react";
import { WagmiProvider, createConfig, http } from "wagmi";
import { base, baseSepolia } from "wagmi/chains";
import { injected, coinbaseWallet, walletConnect } from "wagmi/connectors";

const walletConnectProjectId = import.meta.env.VITE_WALLETCONNECT_PROJECT_ID as string | undefined;

// Build connectors array
const connectors = [
  injected(),
  coinbaseWallet({
    appName: "AEGIS Protocol",
    appLogoUrl: "https://aegis.protocol/logo.png",
  }),
];

// Add WalletConnect if project ID is configured
if (walletConnectProjectId) {
  connectors.push(
    walletConnect({
      projectId: walletConnectProjectId,
      showQrModal: true,
      metadata: {
        name: "AEGIS Protocol",
        description: "AI-Enhanced Guardian Intelligence System for DeFi",
        url: "https://aegis.protocol",
        icons: ["https://aegis.protocol/logo.png"],
      },
    })
  );
}

export const wagmiConfig = createConfig({
  chains: [baseSepolia, base],
  connectors,
  transports: {
    [baseSepolia.id]: http(),
    [base.id]: http(),
  },
});

export function Web3Provider({ children }: { children: ReactNode }) {
  return <WagmiProvider config={wagmiConfig}>{children}</WagmiProvider>;
}
