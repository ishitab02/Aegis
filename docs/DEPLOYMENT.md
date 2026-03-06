# AEGIS Protocol - Deployment Guide

## Architecture Overview

AEGIS consists of 3 services that need to be deployed:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    FRONTEND     │────▶│   TS API        │────▶│  PYTHON AGENTS  │
│    (Vercel)     │     │ (Railway/Vercel)│     │   (Railway)     │
│   Port: 443     │     │   Port: 3000    │     │   Port: 8000    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Option 1: Full Stack on Railway (Recommended)

Railway supports both Node.js and Python, making it ideal for AEGIS.

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your AEGIS repository

### Step 2: Deploy Python Agents

```bash
# In Railway dashboard, create a new service
Service Name: aegis-agents
Root Directory: packages/agents-py
Build Command: pip install -r requirements.txt
Start Command: uvicorn aegis.api.server:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
```
ANTHROPIC_API_KEY=sk-ant-...
BASE_SEPOLIA_RPC=https://sepolia.base.org
PORT=8000
```

### Step 3: Deploy TypeScript API

```bash
Service Name: aegis-api
Root Directory: packages/api
Build Command: pnpm install && pnpm build
Start Command: node dist/index.js
```

**Environment Variables:**
```
AGENT_API_URL=https://aegis-agents-production.up.railway.app
BASE_SEPOLIA_RPC=https://sepolia.base.org
CIRCUIT_BREAKER_ADDRESS=0xa0eE49660252B353830ADe5de0Ca9385647F85b5
TELEGRAM_BOT_TOKEN=your-bot-token (optional)
TELEGRAM_CHAT_ID=your-chat-id (optional)
PORT=3000
```

### Step 4: Deploy Frontend to Vercel

See "Frontend on Vercel" section below.

---

## Option 2: Frontend on Vercel + Backend on Railway

### Deploy Frontend to Vercel

#### Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to frontend
cd packages/frontend

# Deploy
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: aegis-frontend
# - Framework: Vite
# - Build command: pnpm build
# - Output directory: dist
```

#### Via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `packages/frontend`
   - **Build Command**: `pnpm build`
   - **Output Directory**: `dist`

5. Add Environment Variables:
   ```
   VITE_API_URL=https://aegis-api-production.up.railway.app
   ```

6. Click "Deploy"

### Vercel Configuration

The `packages/frontend/vercel.json` is already configured:

```json
{
  "buildCommand": "pnpm build",
  "outputDirectory": "dist",
  "framework": "vite",
  "env": {
    "VITE_API_URL": "@vite_api_url"
  }
}
```

---

## Option 3: All Services on Vercel (Serverless)

⚠️ **Note**: Python agents require a separate deployment. Vercel's Python runtime has limitations.

### Deploy TS API as Vercel Functions

Create `packages/api/vercel.json`:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "src/index.ts",
      "use": "@vercel/node"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "src/index.ts"
    }
  ]
}
```

Then deploy:

```bash
cd packages/api
vercel
```

---

## Environment Variables Reference

### Python Agents (aegis-agents)

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key for AI analysis |
| `BASE_SEPOLIA_RPC` | Yes | RPC URL for Base Sepolia |
| `PORT` | Yes | Server port (Railway sets automatically) |

### TypeScript API (aegis-api)

| Variable | Required | Description |
|----------|----------|-------------|
| `AGENT_API_URL` | Yes | URL of Python agents service |
| `BASE_SEPOLIA_RPC` | Yes | RPC URL for Base Sepolia |
| `CIRCUIT_BREAKER_ADDRESS` | No | Contract address (has default) |
| `TELEGRAM_BOT_TOKEN` | No | For alert notifications |
| `TELEGRAM_CHAT_ID` | No | Telegram chat for alerts |
| `API_KEYS` | No | Comma-separated API keys for auth |
| `PORT` | Yes | Server port |

### Frontend (aegis-frontend)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | URL of TypeScript API |

---

## Post-Deployment Checklist

- [ ] All three services are running
- [ ] Frontend can reach TS API (check browser console)
- [ ] TS API can reach Python agents (check `/api/v1/health`)
- [ ] Chainlink Data Feeds are accessible
- [ ] Circuit breaker contract is callable
- [ ] Telegram notifications work (if configured)

### Verify Deployment

```bash
# Check Python agents
curl https://aegis-agents-production.up.railway.app/api/v1/health

# Check TS API
curl https://aegis-api-production.up.railway.app/api/v1/health

# Check frontend
# Open https://aegis-frontend.vercel.app in browser
```

---

## Domain Configuration

### Custom Domain on Vercel

1. Go to Project Settings → Domains
2. Add your domain (e.g., `aegis.xyz`)
3. Configure DNS:
   ```
   Type: CNAME
   Name: @
   Value: cname.vercel-dns.com
   ```

### Custom Domain on Railway

1. Go to Service Settings → Networking
2. Add custom domain
3. Configure DNS as shown

---

## Cost Estimates

| Platform | Free Tier | Paid |
|----------|-----------|------|
| **Vercel** | 100GB bandwidth, unlimited deploys | $20/mo Pro |
| **Railway** | $5 free credits/mo | $0.000463/min (~$20/mo for always-on) |

### Budget-Friendly Setup

1. Frontend on Vercel (free)
2. TS API on Railway ($10/mo)
3. Python Agents on Railway ($10/mo)

**Total: ~$20/month** for production deployment

---

## Troubleshooting

### CORS Errors

Add your frontend URL to the TS API CORS config in `packages/api/src/index.ts`:

```typescript
app.use(
  cors({
    origin: [
      "http://localhost:5173",
      "https://aegis-frontend.vercel.app",
      "https://aegis.xyz"
    ],
  })
);
```

### API Connection Failed

1. Check that `VITE_API_URL` is set correctly in Vercel
2. Ensure the TS API is running on Railway
3. Check Railway logs for errors

### Python Agents Not Responding

1. Check Railway logs: `railway logs`
2. Verify `ANTHROPIC_API_KEY` is set
3. Ensure port binding: `--host 0.0.0.0 --port $PORT`
