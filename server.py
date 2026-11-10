"""
SheetLink-MCP: Universal Google Sheets Bridge
Author: Saikat (https://github.com/saikatcloudhere)
Repository: https://github.com/saikatcloudhere/SheetLink-MCP

Compatible with:
- Claude Desktop
- Cursor IDE
- Google Antigravity
- OpenAI Codex / VS Code
"""

import os
import json
import sys
from typing import List, Optional, Any, Union
import requests

# Dual MCP SDK Compatibility: Supports both mcp 2.x and mcp 1.x
try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise RuntimeError("The 'mcp' package is required. Run 'pip install \"mcp[cli]>=1.0.0\"'.")

# Initialize Server
mcp = FastMCP("SheetLink-MCP")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def get_sheet_url() -> str:
    """Retrieves the deployed Google Sheet Web App URL from config.json or environment."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                url = data.get("sheet_url", "").strip()
                if url:
                    return url
        except Exception:
            pass
    return os.getenv("GOOGLE_SHEET_WEBAPP_URL", "").strip()


def normalize_row_data(row_data: Any) -> List[str]:
    """
    Normalizes diverse LLM inputs (lists, JSON strings, comma-separated strings)
    into a clean list of string cell values.
    """
    if isinstance(row_data, str):
        cleaned = row_data.strip()
        # Handle stringified list like '["A", "B"]'
        if (cleaned.startswith("[") and cleaned.endswith("]")) or (cleaned.startswith("(") and cleaned.endswith(")")):
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except Exception:
                pass
        # Handle comma-separated string like 'Tanvir, 017..., Paid'
        if "," in cleaned:
            return [part.strip() for part in cleaned.split(",") if part.strip()]
        return [cleaned]
    elif isinstance(row_data, (list, tuple)):
        return [str(x) for x in row_data]
    return [str(row_data)]


def make_request(method: str, payload: Optional[dict] = None) -> dict:
    """Helper to perform HTTP requests with automatic 302 redirect handling."""
    url = get_sheet_url()
    if not url:
        return {
            "status": "error",
            "message": "Google Sheet URL is not configured. Please run setup_wizard.py or configure config.json."
        }

    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SheetLink-MCP/1.0"
        }
        if method == "GET":
            params = payload if payload else {}
            response = requests.get(url, params=params, headers=headers, timeout=15, allow_redirects=True)
        else:
            response = requests.post(url, json=payload, headers=headers, timeout=15, allow_redirects=True)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Connection to Google Sheet timed out after 15 seconds. Please try again."
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Network communication failure: {str(e)}"
        }
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "Invalid JSON response received from Google Apps Script."
        }


@mcp.tool()
def read_sheet_records(sheet_name: Optional[str] = None) -> str:
    """
    Reads and returns all existing rows and columns from the Google Sheet.
    Args:
        sheet_name: (Optional) Name of the worksheet tab to read (e.g. 'Sales', 'Sheet1').
                    Defaults to the active worksheet tab.
    """
    payload = {}
    if sheet_name:
        payload["sheet_name"] = sheet_name

    res = make_request("GET", payload)
    if res.get("status") == "success":
        return json.dumps({
            "worksheet": res.get("sheet_name", "Active Sheet"),
            "total_rows": res.get("total_rows", 0),
            "rows": res.get("data", [])
        }, ensure_ascii=False)
    return f"Error: {res.get('message', 'Failed to read sheet')}"


@mcp.tool()
def append_new_row(row_data: Union[List[str], str], sheet_name: Optional[str] = None) -> str:
    """
    Appends a new row of values to the Google Sheet.
    Args:
        row_data: List of cell values or comma-separated string to add as a new row.
                  Example: ["Tanvir Ahmed", "01711223344", "Dhaka", "$4,500", "Paid"]
        sheet_name: (Optional) Target worksheet tab name. Defaults to active tab.
    """
    cleaned_rows = normalize_row_data(row_data)
    if not cleaned_rows:
        return "Error: row_data cannot be empty."

    payload = {
        "action": "append_row",
        "row_data": cleaned_rows
    }
    if sheet_name:
        payload["sheet_name"] = sheet_name

    res = make_request("POST", payload)
    if res.get("status") == "success":
        tab_info = f" in '{res.get('sheet_name')}'" if res.get('sheet_name') else ""
        return f"✅ Row successfully appended{tab_info}! Total rows: {res.get('row_count', 'N/A')}."
    return f"Error: {res.get('message', 'Failed to append row')}"


@mcp.tool()
def update_cell_by_search(search_text: str, column_index: int, new_value: str, sheet_name: Optional[str] = None) -> str:
    """
    Searches for a specific text/identifier in the sheet and updates a target column in the matching row.
    Args:
        search_text: Value to find (e.g. customer name, email, or invoice ID).
        column_index: 1-based column number to update (1 = Column A, 2 = Column B, etc.).
        new_value: New value to set in that cell.
        sheet_name: (Optional) Target worksheet tab name. Defaults to active tab.
    """
    payload = {
        "action": "update_cell",
        "search_text": str(search_text),
        "column_index": int(column_index),
        "new_value": str(new_value)
    }
    if sheet_name:
        payload["sheet_name"] = sheet_name

    res = make_request("POST", payload)
    if res.get("status") == "success":
        return f"✅ {res.get('message', 'Cell updated successfully.')}"
    return f"Error: {res.get('message', 'Update failed')}"


@mcp.tool()
def search_records(query: str, sheet_name: Optional[str] = None) -> str:
    """
    Searches through all rows in the sheet and returns only the rows containing the search query.
    Args:
        query: Keyword, name, phone, or status to search for.
        sheet_name: (Optional) Target worksheet tab name.
    """
    payload = {}
    if sheet_name:
        payload["sheet_name"] = sheet_name

    res = make_request("GET", payload)
    if res.get("status") != "success":
        return f"Error: {res.get('message')}"

    all_data = res.get("data", [])
    if not all_data:
        return "Sheet is empty."

    query_lower = query.lower()
    matching_rows = []
    headers = all_data[0] if all_data else []

    for row in all_data:
        row_str = " ".join(str(cell) for cell in row).lower()
        if query_lower in row_str:
            matching_rows.append(row)

    if not matching_rows:
        return f"No records found matching query: '{query}'"

    return json.dumps({
        "worksheet": res.get("sheet_name", "Active Sheet"),
        "query": query,
        "matches_found": len(matching_rows),
        "headers": headers,
        "results": matching_rows
    }, ensure_ascii=False)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
