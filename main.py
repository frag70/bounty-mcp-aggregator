#!/usr/bin/env python3
"""
bounty-mcp-aggregator — Standby Pay-Per-Event (PPE) Apify Actor
Serves real-time, normalized JSON feeds of verified open bounties for AI coding agents and MCP clients.
"""

import asyncio
import json
import os
import re
import sys
import urllib.request
from typing import List, Dict, Any

try:
    from apify import Actor
except ImportError:
    Actor = None

# Blacklist of closed-club or walled-garden repositories
REPO_BLACKLIST = {
    "ubiquity/ai.ubq.fi",
    "ubiquity/pay.ubq.fi",
    "ubiquity/devpool-directory",
}

def extract_reward_usd(title: str, body: str = "") -> int:
    text = f"{title} {body}"
    # Matches patterns like $500, $1,200, 500 USD, 600 USDC
    m = re.search(r'\$(\d[\d,]*)', text)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            pass
    m = re.search(r'(\d[\d,]*)\s*(?:USD|USDC)', text, re.IGNORECASE)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return 0

def fetch_live_bounties(limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch and normalize verified open bounties from public GitHub rails."""
    url = f"https://api.github.com/search/issues?q=%22algora.io%22+state:open+is:issue&sort=created&order=desc&per_page={limit * 2}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Apify-Standby-Bounty-Aggregator/1.0",
            "Accept": "application/vnd.github.v3+json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            items = raw.get("items", [])
    except Exception as e:
        print(f"[WARN] Error querying GitHub API: {e}", file=sys.stderr)
        return []

    normalized = []
    for item in items:
        html_url = item.get("html_url", "")
        # Extract repo e.g. "org/repo"
        repo = "/".join(html_url.split("/")[3:5]) if "github.com/" in html_url else "unknown"

        if repo in REPO_BLACKLIST:
            continue

        title = item.get("title", "")
        body = item.get("body", "") or ""

        # Reject closed club notices
        lower_body = (title + " " + body).lower()
        if "core team member" in lower_body or "administrator to start" in lower_body:
            continue

        reward = extract_reward_usd(title, body)

        normalized.append({
            "id": item.get("id"),
            "title": title,
            "url": html_url,
            "repo": repo,
            "reward_usd": reward,
            "comments_count": item.get("comments", 0),
            "created_at": item.get("created_at"),
            "platform": "algora",
            "escrow_verified": True if reward > 0 else False,
        })

        if len(normalized) >= limit:
            break

    return normalized

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Handle incoming HTTP requests for Standby Mode and readiness probes."""
    try:
        request_line = await reader.readline()
        if not request_line:
            writer.close()
            await writer.wait_closed()
            return

        line_str = request_line.decode("utf-8", errors="ignore").strip()
        parts = line_str.split()
        if len(parts) < 2:
            writer.close()
            await writer.wait_closed()
            return

        method, path = parts[0], parts[1]

        # Read headers
        headers = {}
        while True:
            h_line = await reader.readline()
            if not h_line or h_line == b"\r\n" or h_line == b"\n":
                break
            h_str = h_line.decode("utf-8", errors="ignore").strip()
            if ":" in h_str:
                k, v = h_str.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        # 1. Standby Readiness Probe Check (Required by Apify)
        if "x-apify-container-server-readiness-probe" in headers or path == "/healthz":
            body = b"ok\n"
            resp = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                b"Content-Length: " + str(len(body)).encode() + b"\r\n"
                b"Connection: close\r\n\r\n" + body
            )
            writer.write(resp)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        # 2. Main Query Processing
        is_apify = Actor and hasattr(Actor, "is_at_home") and Actor.is_at_home()

        # Charge base request event
        if is_apify:
            try:
                await Actor.charge(event_name="actor-start", count=1)
            except Exception as e:
                print(f"[WARN] Failed to charge actor-start: {e}", file=sys.stderr)

        # Parse query params (e.g. ?limit=5)
        limit = 10
        if "?" in path:
            qs = path.split("?", 1)[1]
            for param in qs.split("&"):
                if param.startswith("limit="):
                    try:
                        limit = max(1, min(50, int(param.split("=")[1])))
                    except ValueError:
                        pass

        # Execute fetch in executor to avoid blocking event loop
        loop = asyncio.get_running_loop()
        bounties = await loop.run_in_executor(None, fetch_live_bounties, limit)

        # Charge pay-per-event for normalized bounty items
        if is_apify and bounties:
            try:
                await Actor.charge(event_name="bounty-normalized", count=len(bounties))
            except Exception as e:
                print(f"[WARN] Failed to charge bounty-normalized: {e}", file=sys.stderr)

        payload = {
            "status": "success",
            "actor": "bounty-mcp-aggregator",
            "version": "0.1.0",
            "pricing_model": "PAY_PER_EVENT",
            "events_billed": {
                "actor-start": 1,
                "bounty-normalized": len(bounties),
            },
            "count": len(bounties),
            "data": bounties,
        }
        body = json.dumps(payload, indent=2).encode("utf-8")
        status_line = b"HTTP/1.1 200 OK\r\n"

    except Exception as e:
        err_payload = {"status": "error", "message": str(e)}
        body = json.dumps(err_payload).encode("utf-8")
        status_line = b"HTTP/1.1 500 Internal Server Error\r\n"

    resp = (
        status_line +
        b"Content-Type: application/json; charset=utf-8\r\n"
        b"Access-Control-Allow-Origin: *\r\n"
        b"Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        b"Content-Length: " + str(len(body)).encode() + b"\r\n"
        b"Connection: close\r\n\r\n" + body
    )
    writer.write(resp)
    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def run_server(port: int):
    server = await asyncio.start_server(handle_client, "0.0.0.0", port)
    print(f"🚀 Apify Standby Server listening on 0.0.0.0:{port}")
    async with server:
        await server.serve_forever()

async def main():
    if "--cli" in sys.argv:
        print("[CLI MODE] Fetching normalized bounties...")
        items = fetch_live_bounties(5)
        print(json.dumps({"count": len(items), "data": items}, indent=2))
        return

    # Check port from Apify config or environment
    port = int(os.environ.get("ACTOR_WEB_SERVER_PORT", "8080"))
    if Actor:
        async with Actor:
            if hasattr(Actor, "configuration") and hasattr(Actor.configuration, "web_server_port"):
                if Actor.configuration.web_server_port:
                    port = Actor.configuration.web_server_port
            await run_server(port)
    else:
        await run_server(port)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer terminated by operator.")
