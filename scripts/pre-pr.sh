#!/usr/bin/env bash
# pre-pr checks: run before pushing to catch CI failures locally
# usage: bash scripts/pre-pr.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # no color
BOLD='\033[1m'

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0
SKIP=0
RESULTS=()

step() {
  echo ""
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BOLD}  $1${NC}"
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

pass() {
  echo -e "  ${GREEN}✓ $1${NC}"
  RESULTS+=("${GREEN}✓${NC} $1")
  PASS=$((PASS + 1))
}

fail() {
  echo -e "  ${RED}✗ $1${NC}"
  RESULTS+=("${RED}✗${NC} $1")
  FAIL=$((FAIL + 1))
}

skip() {
  echo -e "  ${YELLOW}⊘ $1 (skipped)${NC}"
  RESULTS+=("${YELLOW}⊘${NC} $1 (skipped)")
  SKIP=$((SKIP + 1))
}

step "1/6  Solidity formatting (forge fmt)"

if command -v forge &>/dev/null; then
  cd "$ROOT/packages/contracts"
  if forge fmt --check 2>/dev/null; then
    pass "Solidity formatting"
  else
    fail "Solidity formatting — run: cd packages/contracts && forge fmt"
  fi
else
  skip "Solidity formatting — forge not installed"
fi

step "2/6  Solidity tests (forge test)"

if command -v forge &>/dev/null; then
  cd "$ROOT/packages/contracts"
  if forge test --no-match-path "test/Integration.t.sol" 2>&1 | tail -1 | grep -q "passed"; then
    pass "Solidity tests"
  else
    fail "Solidity tests — run: cd packages/contracts && forge test -vvv"
  fi
else
  skip "Solidity tests — forge not installed"
fi

step "3/6  Python linting (ruff)"

cd "$ROOT/packages/agents-py"
if [ -d "venv" ]; then
  source venv/bin/activate 2>/dev/null || true
fi

if command -v ruff &>/dev/null; then
  if ruff check aegis/ tests/ --select E,F,I --ignore E501; then
    pass "Python linting"
  else
    fail "Python linting — run: cd packages/agents-py && ruff check aegis/ tests/ --select E,F,I --ignore E501 --fix"
  fi
else
  skip "Python linting — ruff not installed (pip install ruff)"
fi

step "4/6  Python tests (pytest)"

cd "$ROOT/packages/agents-py"
if python -m pytest tests/ -v --tb=short 2>&1 | tail -1 | grep -q "passed"; then
  pass "Python tests (96)"
else
  fail "Python tests — run: cd packages/agents-py && python -m pytest tests/ -v"
fi

step "5/6  TypeScript formatting (prettier)"

cd "$ROOT"
if npx prettier --check \
  "packages/api/src/**/*.ts" \
  "packages/cre-workflows/src/**/*.ts" \
  "packages/frontend/src/**/*.{ts,tsx}" 2>/dev/null; then
  pass "TypeScript formatting"
else
  fail "TypeScript formatting — run: npx prettier --write \"packages/api/src/**/*.ts\" \"packages/cre-workflows/src/**/*.ts\" \"packages/frontend/src/**/*.{ts,tsx}\""
fi

step "6/6  TypeScript typecheck + frontend build"

cd "$ROOT"
TS_OK=true

echo "  Typechecking packages/api..."
if (cd packages/api && npx tsc --noEmit 2>&1); then
  echo -e "  ${GREEN}  api ✓${NC}"
else
  echo -e "  ${RED}  api ✗${NC}"
  TS_OK=false
fi

echo "  Typechecking packages/cre-workflows..."
if (cd packages/cre-workflows && npx tsc --noEmit 2>&1); then
  echo -e "  ${GREEN}  cre-workflows ✓${NC}"
else
  echo -e "  ${RED}  cre-workflows ✗${NC}"
  TS_OK=false
fi

echo "  Building packages/frontend..."
if (cd packages/frontend && npx vite build 2>&1 | tail -3); then
  echo -e "  ${GREEN}  frontend ✓${NC}"
else
  echo -e "  ${RED}  frontend ✗${NC}"
  TS_OK=false
fi

if $TS_OK; then
  pass "TypeScript typecheck + frontend build"
else
  fail "TypeScript typecheck + frontend build"
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  RESULTS${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
for r in "${RESULTS[@]}"; do
  echo -e "  $r"
done
echo ""
echo -e "  ${GREEN}Passed: $PASS${NC}  ${RED}Failed: $FAIL${NC}  ${YELLOW}Skipped: $SKIP${NC}"
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo -e "${RED}${BOLD}  ✗ Pre-PR checks failed. Fix the issues above before pushing.${NC}"
  echo ""
  exit 1
else
  echo -e "${GREEN}${BOLD}  ✓ All pre-PR checks passed. Ready to push!${NC}"
  echo ""
  exit 0
fi
