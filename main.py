#!/usr/bin/env python3
"""Zero-Proxy Standby PPE Actor: Normalizes live GitHub/Algora bounties for AI coding agents."""
import json, urllib.request

def fetch_normalized_bounties():
    url = "https://api.github.com/search/issues?q=%22algora.io%22+state:open+is:issue&per_page=10"
    req = urllib.request.Request(url, headers={"User-Agent": "Apify-PPE-Standby-Actor/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        items = json.loads(resp.read().decode("utf-8")).get("items", [])
    return [{"id": i["id"], "title": i["title"], "url": i["html_url"], "comments": i["comments"]} for i in items]

if __name__ == "__main__":
    results = fetch_normalized_bounties()
    print(json.dumps({"event_charged": "bounty-normalized", "count": len(results), "data": results}, indent=2))
