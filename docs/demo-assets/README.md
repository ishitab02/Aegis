# Demo Assets

This directory contains visual assets for the AEGIS demo video.

## Files

- `ARCHITECTURE.md` - ASCII architecture diagrams
- Screenshots should be added here before recording

## Screenshots to Capture

Before recording the demo video, capture these screenshots:

1. **dashboard-healthy.png** - Dashboard showing all green status
2. **dashboard-critical.png** - Dashboard after attack detection
3. **ccip-explorer.png** - CCIP Explorer showing delivered message
4. **vrf-basescan.png** - VRF request transaction on BaseScan
5. **testvault-paused.png** - TestVault showing paused state
6. **forensics-euler.png** - Euler hack analysis output

## How to Capture

1. Start services: `bash scripts/run-demo.sh`
2. Open dashboard: http://localhost:5173
3. Take screenshot of healthy state
4. Run detection: `npx tsx scripts/run-full-demo.ts`
5. Take screenshot of critical state
6. Open CCIP Explorer and screenshot
7. etc.
