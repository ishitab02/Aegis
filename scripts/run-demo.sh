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

# ---- Kill any existing processes on our ports ----
echo -e "${YELLOW}Cleaning up any existing processes...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
sleep 1

# ---- 1. Start Python Agent API (port 8000) ----
echo -e "${BLUE}[1/3] Starting Python Agent API on port 8000...${NC}"
cd "$ROOT_DIR/packages/agents-py"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
  source venv/bin/activate
fi

uvicorn aegis.api.server:app --host 0.0.0.0 --port 8000 --log-level info &
PID_AGENT=$!
sleep 3

# Verify Python API is running
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
  echo -e "${GREEN}  Python Agent API started successfully${NC}"
else
  echo -e "${RED}  Warning: Python API may not be responding${NC}"
fi

# ---- 2. Start TypeScript API (port 3000) ----
echo -e "${BLUE}[2/3] Starting TypeScript API on port 3000...${NC}"
cd "$ROOT_DIR/packages/api"
npx tsx src/index.ts &
PID_API=$!
sleep 2

# Verify TS API is running
if curl -s http://localhost:3000/ > /dev/null 2>&1; then
  echo -e "${GREEN}  TypeScript API started successfully${NC}"
else
  echo -e "${RED}  Warning: TypeScript API may not be responding${NC}"
fi

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
echo -e "  Dashboard:    ${BLUE}http://localhost:5173${NC}"
echo -e "  Demo Page:    ${BLUE}http://localhost:5173/demo${NC}"
echo -e "  TS API:       ${BLUE}http://localhost:3000${NC}"
echo -e "  Agent API:    ${BLUE}http://localhost:8000${NC}"
echo -e "  API Docs:     ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  Swagger Docs: ${BLUE}http://localhost:3000/api/v1/docs${NC}"
echo ""
echo -e "${YELLOW}Available endpoints:${NC}"
echo "  GET  /api/v1/demo/scenarios           - List demo scenarios"
echo "  POST /api/v1/demo/euler-replay        - Start Euler exploit replay"
echo "  GET  /api/v1/demo/euler-replay/step/N - Get step N of replay"
echo ""
echo -e "${YELLOW}To test the demo API:${NC}"
echo "  curl http://localhost:3000/api/v1/demo/scenarios"
echo "  curl -X POST http://localhost:3000/api/v1/demo/euler-replay"
echo ""
echo -e "Press Ctrl+C to stop all services."

wait
