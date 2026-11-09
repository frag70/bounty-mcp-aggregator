# Verified Bounty & Agent Task Normalizer (Apify Standby PPE)

A blazing-fast, zero-proxy Standby Apify Actor providing real-time, normalized JSON feeds of verified open bounties for AI coding agents and Model Context Protocol (MCP) clients.

## ⚡ Key Highlights
- **Standby Mode:** Pre-warmed HTTP endpoint responding in milliseconds with 0 MB idle RAM cost.
- **Pay-Per-Event (PPE):** Micro-metered pricing at $0.0001 per request + $0.002 per normalized verified bounty.
- **Agent-Ready Schema:** Sanitized JSON with escrow checks, title, issue URLs, and dollar amounts.
- **Noise Filtered:** Automatically strips walled gardens, private repository invites, and closed tasks.

## 📡 API Usage & Standby Endpoint

### 1. Readiness Check (Health Check)
```bash
curl -I -H "x-apify-container-server-readiness-probe: 1" "https://<actor-standby-url>"
# Returns: 200 OK
```

### 2. Query Live Bounties
```bash
curl "https://<actor-standby-url>?limit=5"
```

Sample Response:
```json
{
  "status": "success",
  "actor": "bounty-mcp-aggregator",
  "version": "0.1.0",
  "pricing_model": "PAY_PER_EVENT",
  "events_billed": {
    "actor-start": 1,
    "bounty-normalized": 3
  },
  "count": 3,
  "data": [
    {
      "id": 18294719,
      "title": "💎 [Escrowed $600 USDC] 24-Vector Conformance Suite",
      "url": "https://github.com/example/repo/issues/2",
      "repo": "example/repo",
      "reward_usd": 600,
      "comments_count": 4,
      "created_at": "2026-11-09T18:00:00Z",
      "platform": "algora",
      "escrow_verified": true
    }
  ]
}
```

## 🛠️ Deploy to Apify Store
1. Open [Apify Console](https://console.apify.com/actors/new).
2. Choose **Git repository** -> Link `https://github.com/frag70/bounty-mcp-aggregator`.
3. Click **Build & Publish** to list on the Apify Store.
