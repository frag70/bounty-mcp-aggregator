# Open-Source Bounty & Agent Skill MCP Normalizer (Standby PPE)

A ultra-fast, zero-proxy Apify Actor designed to deliver normalized open-source bounties (Algora, Ubiquity DevPool, Polar.sh) formatted for AI coding agents and Model Context Protocol (MCP) clients.

## ⚡ Key Highlights
- **Standby Mode:** Responds in milliseconds with 0 MB idle RAM.
- **Pay-Per-Event (PPE):** Ultra-low pricing at $0.002 per normalized query event.
- **Agent-Ready Output:** Clean JSON with repository URLs, dollar rewards, escrow verification, and target issues.

## 💰 Monetization & Usage
Run this actor on demand via Apify REST API:
```bash
curl -X POST "https://api.apify.com/v2/acts/<YOUR_USERNAME>~bounty-mcp-aggregator/run-sync?token=<YOUR_TOKEN>"
```

Output:
```json
{
  "event_charged": "bounty-normalized",
  "price_usd": 0.002,
  "count": 3,
  "data": [
    {
      "id": 6006126694,
      "title": "Preserve 502 for exchange transport failures",
      "url": "https://github.com/ubiquity/ai.ubq.fi/issues/1282",
      "repo": "ubiquity/ai.ubq.fi",
      "reward_usd": 75,
      "platform": "ubiquity-devpool",
      "escrow_verified": true
    }
  ]
}
```
