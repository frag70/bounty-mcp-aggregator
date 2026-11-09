#!/usr/bin/env python3
"""
deploy.py — Turnkey Deployer for Apify Standby PPE Actor: 'bounty-mcp-aggregator'
Part of Autonomous Engine (Arena 2: Apify Store)

Usage:
  python3 staging/apify_actors/bounty-mcp-aggregator/deploy.py
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ACTOR_DIR = Path(__file__).parent.resolve()
ACTOR_JSON = ACTOR_DIR / ".actor" / "actor.json"
MAIN_PY = ACTOR_DIR / "main.py"


def check_prerequisites():
    if not ACTOR_JSON.exists():
        print(f"❌ Error: {ACTOR_JSON} not found!")
        sys.exit(1)
    if not MAIN_PY.exists():
        print(f"❌ Error: {MAIN_PY} not found!")
        sys.exit(1)

    spec = json.loads(ACTOR_JSON.read_text(encoding="utf-8"))
    print(f"✅ Verified Actor Specification:")
    print(f"   Name: {spec.get('name')}")
    print(f"   Title: {spec.get('title')}")
    print(f"   Standby Mode: {spec.get('usesStandbyMode')}")
    print(f"   Pricing Model: {spec.get('pricingInfo', {}).get('pricingModel')}")


def get_apify_token() -> str:
    token = os.getenv("APIFY_TOKEN")
    if not token:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("APIFY_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    return token or ""


def deploy():
    check_prerequisites()
    token = get_apify_token()

    print("\n--- 🚀 DEPLOYMENT OPTIONS ---")
    apify_cli = shutil.which("apify")

    if apify_cli:
        print(f"1. Apify CLI detected: {apify_cli}")
        print("   Running: apify push ...")
        res = subprocess.run([apify_cli, "push"], cwd=ACTOR_DIR)
        if res.returncode == 0:
            print("\n🎉 Actor successfully pushed to Apify Console!")
            return
        print("⚠️ CLI push returned non-zero code. Checking web console fallback...")

    print("2. Manual / Web Console Deployment (Zero Dependency):")
    print("   a) Open Apify Console: https://console.apify.com/actors/new")
    print("   b) Click 'Create from scratch' -> Name: 'bounty-mcp-aggregator'")
    print("   c) In the Source code tab, upload or paste:")
    print(f"      - {ACTOR_JSON}")
    print(f"      - {MAIN_PY}")
    print("   d) Enable Standby Mode & Set Pricing to Pay-Per-Event ($0.002 / bounty-normalized)")
    print("   e) Click 'Build' and then 'Publish to Apify Store'!")
    print("\n   Store URL: https://apify.com/store")


if __name__ == "__main__":
    deploy()
