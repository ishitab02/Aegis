#!/bin/bash
# =============================================================================
# AEGIS Protocol - Demo Runner
# Starts all 3 services and opens the dashboard.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "================================================"
echo "  AEGIS Protocol - DeFi Security Demo"
echo "  AI-Enhanced Guardian Intelligence System"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

cleanup() {
  echo ""
  echo -e "${YELLOW}Shutting down AEGIS services...${NC}"
  kill $PID_AGENT 2>/dev/null || true
  kill $PID_API 2>/dev/null || true
  kill $PID_FRONTEND 2>/dev/null || true
  echo -e "${GREEN}All services stopped.${NC}"
  exit 0
}
trap cleanup SIGINT SIGTERM

# ---- 1. Start Python Agent API (port 8000) ----
echo -e "${BLUE}[1/3] Starting Python Agent API on port 8000...${NC}"
cd "$ROOT_DIR/packages/agents-py"
uvicorn aegis.api.server:app --host 0.0.0.0 --port 8000 --log-level info &
PID_AGENT=$!
sleep 2

# ---- 2. Start TypeScript API (port 3000) ----
echo -e "${BLUE}[2/3] Starting TypeScript API on port 3000...${NC}"
cd "$ROOT_DIR/packages/api"
npx tsx src/index.ts &
PID_API=$!
sleep 1

# ---- 3. Start Frontend (port 5173) ----
echo -e "${BLUE}[3/3] Starting Frontend Dashboard on port 5173...${NC}"
cd "$ROOT_DIR/packages/frontend"
npx vite --host &
PID_FRONTEND=$!
sleep 2

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  AEGIS Protocol is running!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "  Dashboard:   ${BLUE}http://localhost:5173${NC}"
echo -e "  TS API:      ${BLUE}http://localhost:3000${NC}"
echo -e "  Agent API:   ${BLUE}http://localhost:8000${NC}"
echo -e "  API Docs:    ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}To simulate an exploit, run in another terminal:${NC}"
echo "  npx tsx scripts/simulate-exploit.ts"
echo ""
echo -e "Press Ctrl+C to stop all services."

wait
