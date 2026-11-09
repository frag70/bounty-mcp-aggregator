#!/usr/bin/env python3
"""
apify_api_deploy.py — Direct API Automated Deployer for Apify Standby PPE Actor
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

REPO_URL = "https://github.com/frag70/bounty-mcp-aggregator#main"
ACTOR_NAME = "bounty-mcp-aggregator"
ACTOR_TITLE = "Verified Bounty & Agent Task Normalizer (Standby API)"
ACTOR_DESC = "Real-time Standby API serving normalized, deduplicated feeds of verified open bounties for AI coding agents."

def get_token(args_token: str = None) -> str:
    if args_token:
        return args_token
    token = os.environ.get("APIFY_TOKEN")
    if token:
        return token
    env_file = Path("/home/thomas/autonomous-engine/.env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("APIFY_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

def api_call(endpoint: str, token: str, method: str = "GET", data: dict = None):
    url = f"https://api.apify.com/v2/{endpoint}?token={token}"
    req = urllib.request.Request(
        url,
        method=method,
        headers={"Content-Type": "application/json"}
    )
    body = json.dumps(data).encode("utf-8") if data else None
    with urllib.request.urlopen(req, data=body, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def deploy_actor(token: str):
    if not token:
        print("❌ Error: No APIFY_TOKEN provided.")
        print("   Get your personal API token at: https://console.apify.com/account/integrations")
        return False

    print(f"🔑 Verifying Apify API Token...")
    try:
        user_info = api_call("users/me", token)
        username = user_info.get("data", {}).get("username")
        print(f"✅ Authenticated as Apify user: @{username}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

    # Check if actor already exists
    actor_id = None
    try:
        existing = api_call(f"actors/{username}~{ACTOR_NAME}", token)
        actor_id = existing.get("data", {}).get("id")
        print(f"ℹ️ Found existing Actor: {username}~{ACTOR_NAME} (ID: {actor_id})")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"📦 Creating new Actor '{ACTOR_NAME}'...")
            payload = {
                "name": ACTOR_NAME,
                "title": ACTOR_TITLE,
                "description": ACTOR_DESC,
                "restartOnError": False,
                "isPublic": True,
            }
            res = api_call("actors", token, method="POST", data=payload)
            actor_id = res.get("data", {}).get("id")
            print(f"✅ Actor created successfully! ID: {actor_id}")
        else:
            raise

    # Configure Git repo version
    print(f"🔗 Linking Git Repository: {REPO_URL}...")
    version_payload = {
        "versionNumber": "0.1",
        "sourceType": "GIT_REPO",
        "gitRepoUrl": REPO_URL,
        "buildTag": "latest",
    }
    try:
        api_call(f"actors/{actor_id}/versions/0.1", token, method="PUT", data=version_payload)
        print("✅ Version 0.1 configured with Git repo.")
    except urllib.error.HTTPError:
        api_call(f"actors/{actor_id}/versions", token, method="POST", data=version_payload)
        print("✅ Version 0.1 created with Git repo.")

    # Trigger Build
    print("🔨 Triggering container build...")
    build_res = api_call(f"actors/{actor_id}/builds?version=0.1", token, method="POST")
    build_id = build_res.get("data", {}).get("id")
    print(f"🚀 Build initiated! Build ID: {build_id}")
    print(f"\n🎉 Actor is live in your Apify Console!")
    print(f"   Console link: https://console.apify.com/actors/{actor_id}")
    return True

if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else None
    tok = get_token(t)
    if tok:
        deploy_actor(tok)
    else:
        print("Usage: python3 apify_api_deploy.py <APIFY_TOKEN>")
