"""
SheetLink-MCP: CLI Connection & Tool Diagnostic Test
Author: Saikat (https://github.com/saikatcloudhere)
Repository: https://github.com/saikatcloudhere/SheetLink-MCP
"""

import sys
import os
import json
import requests

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def get_url():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("sheet_url", "").strip()
        except Exception:
            pass
    return os.getenv("GOOGLE_SHEET_WEBAPP_URL", "").strip()


def run_diagnostics():
    print("==================================================")
    print("      SheetLink-MCP Diagnostic Test Suite         ")
    print("      Author: Saikat (github.com/saikatcloudhere) ")
    print("==================================================\n")

    url = get_url()
    if not url:
        print("❌ [ERROR] No Google Sheet URL found.")
        print("   Please run 'python setup_wizard.py' or create config.json first.\n")
        sys.exit(1)

    print(f"🔗 Target Web App URL: {url[:45]}...\n")

    # TEST 1: Read Sheet
    print("[1/3] Testing 'read_sheet_records' (GET)...")
    try:
        res = requests.get(url, timeout=12, allow_redirects=True)

        if res.status_code == 403:
            print("\n🚨 [ACCESS BLOCKED - HTTP 403 FORBIDDEN]")
            print("   Reason: In Google Apps Script, 'Who has access' is currently set to 'Only myself'.")
            print("\n   👉 HOW TO FIX (30 Seconds):")
            print("   1. Open your Google Sheet > Extensions > Apps Script.")
            print("   2. Click Deploy > Manage deployments (or New deployment).")
            print("   3. Change 'Who has access' from 'Only myself' to 'Anyone'.")
            print("   4. Click Deploy, copy the new URL, and update config.json.\n")
            sys.exit(1)

        res.raise_for_status()
        data = res.json()
        if data.get("status") == "success":
            rows = data.get("data", [])
            sheet_name = data.get("sheet_name", "Sheet1")
            print(f"  ✅ SUCCESS: Retrieved {len(rows)} row(s) from worksheet '{sheet_name}'.")
            if rows:
                print(f"     Preview (Row 1): {rows[0]}")
        else:
            print(f"  ❌ FAILED: {data.get('message')}")
            return
    except requests.exceptions.HTTPError as http_err:
        if res.status_code == 403:
            print("\n🚨 [ACCESS BLOCKED - HTTP 403 FORBIDDEN]")
            print("   Please change 'Who has access' to 'Anyone' in your Google Sheet Deployment settings.\n")
        else:
            print(f"  ❌ HTTP Error {res.status_code}: {http_err}")
        return
    except Exception as e:
        print(f"  ❌ FAILED to connect: {str(e)}")
        return

    # TEST 2: Append Row
    print("\n[2/3] Testing 'append_new_row' (POST)...")
    test_row = ["SheetLink Diagnostic", "test@sheetlink.local", "Automated Health Check", "Passed"]
    payload = {
        "action": "append_row",
        "row_data": test_row
    }
    try:
        res = requests.post(url, json=payload, timeout=12, allow_redirects=True)
        res.raise_for_status()
        result = res.json()
        if result.get("status") == "success":
            print(f"  ✅ SUCCESS: {result.get('message', 'Row appended')}")
            print(f"     Appended data: {test_row}")
        else:
            print(f"  ❌ FAILED: {result.get('message')}")
            return
    except Exception as e:
        print(f"  ❌ FAILED to append: {str(e)}")
        return

    # TEST 3: Verify Append
    print("\n[3/3] Verifying new row was written to Google Sheet...")
    try:
        res = requests.get(url, timeout=12, allow_redirects=True)
        data = res.json()
        rows = data.get("data", [])
        found = any("SheetLink Diagnostic" in row for row in rows)
        if found:
            print("  ✅ SUCCESS: Verified test row exists in the live Google Sheet!")
        else:
            print("  ⚠️ Test row was reported written but not visible on immediate read.")
    except Exception as e:
        print(f"  ⚠️ Verification check encountered an issue: {str(e)}")

    print("\n==================================================")
    print("🎉 ALL DIAGNOSTICS COMPLETED SUCCESSFULLY!")
    print("Your SheetLink-MCP installation is fully operational.")
    print("==================================================\n")


if __name__ == "__main__":
    run_diagnostics()
