"""
SheetLink-MCP: 1-Click Multi-AI Setup Wizard
Author: Saikat (https://github.com/saikatcloudhere)
Repository: https://github.com/saikatcloudhere/SheetLink-MCP

Supports 1-Click Auto-configuration for:
1. Google Antigravity
2. Claude Desktop
3. OpenAI Codex
"""

import os
import sys
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
SERVER_PATH = os.path.join(CURRENT_DIR, "server.py").replace("\\", "/")
CONFIG_PATH = os.path.join(CURRENT_DIR, "config.json")
SERVER_NAME = "sheetlink-mcp"


def get_safe_python_executable() -> str:
    """Ensures python.exe (with stdin/stdout capability) is used instead of pythonw.exe."""
    exe = sys.executable
    if exe.lower().endswith("pythonw.exe"):
        candidate = exe[:-10] + "python.exe"
        if os.path.exists(candidate):
            return candidate.replace("\\", "/")
    return exe.replace("\\", "/")


def get_claude_config_path() -> str:
    """Returns the platform-specific path to claude_desktop_config.json."""
    if sys.platform == "win32":
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            # The MSIX build can redirect roaming data into its package container.
            packages = Path(local_app_data) / "Packages"
            for package in sorted(packages.glob("Claude_*")):
                roaming = package / "LocalCache" / "Roaming" / "Claude"
                if roaming.is_dir():
                    return str(roaming / "claude_desktop_config.json")
        app_data = os.environ.get("APPDATA")
        if app_data:
            return os.path.join(app_data, "Claude", "claude_desktop_config.json")
    elif sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
    return ""


def get_antigravity_config_path() -> str:
    """Returns the global path to Antigravity's mcp_config.json."""
    user_home = os.path.expanduser("~")
    return os.path.join(user_home, ".gemini", "config", "mcp_config.json")


def get_codex_config_path() -> Path:
    codex_home = os.getenv("CODEX_HOME")
    return (Path(codex_home).expanduser() if codex_home else Path.home() / ".codex") / "config.toml"


def test_url_connection(url: str) -> tuple[bool, str]:
    if not url or not url.startswith("http"):
        return False, "URL must begin with https://"

    try:
        import requests
        res = requests.get(
            url,
            headers={"User-Agent": "SheetLink-MCP-Wizard/1.0"},
            timeout=12,
            allow_redirects=True
        )

        if res.status_code == 403:
            return False, (
                "🚨 HTTP 403 Forbidden: Google Access Blocked!\n\n"
                "Please change 'Who has access' to 'Anyone' in your Google Sheet Deployment settings."
            )

        res.raise_for_status()
        data = res.json()
        if data.get("status") == "success":
            total = data.get("total_rows", len(data.get("data", [])))
            sheet_name = data.get("sheet_name", "Sheet1")
            return True, f"Connection verified! Connected to '{sheet_name}' with {total} row(s)."
        return False, f"Server responded with error: {data.get('message', 'Unknown issue')}"
    except Exception as e:
        return False, f"Could not connect to Google Sheet: {str(e)}"


def write_config(path: Path, content: str):
    """Replace the config only after the complete new content has been written."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as file:
        temporary_path = Path(file.name)
        try:
            file.write(content)
            file.close()
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)


def update_json_file(path: Path, server_config: dict):
    data = json.loads(path.read_text(encoding="utf-8-sig") or "{}") if path.exists() else {}
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    servers = data.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError("Expected mcpServers to be a JSON object")
    servers[SERVER_NAME] = server_config
    write_config(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def update_codex_config(path: Path, server_config: dict):
    import tomlkit

    data = tomlkit.parse(path.read_text(encoding="utf-8")) if path.exists() else tomlkit.document()
    servers = data.setdefault("mcp_servers", tomlkit.table())
    if not isinstance(servers, dict):
        raise ValueError("Expected mcp_servers to be a TOML table")
    servers[SERVER_NAME] = server_config
    write_config(path, tomlkit.dumps(data))


def install_configuration(sheet_url: str, enable_antigravity: bool, enable_claude: bool, enable_codex: bool):
    write_config(Path(CONFIG_PATH), json.dumps({"sheet_url": sheet_url}, indent=2) + "\n")
    server_entry = {"command": get_safe_python_executable(), "args": [SERVER_PATH]}
    results = ["Google Sheet URL saved to config.json."]
    failed = False
    clients = [
        (enable_antigravity, "Google Antigravity", get_antigravity_config_path, update_json_file),
        (enable_claude, "Claude Desktop", get_claude_config_path, update_json_file),
        (enable_codex, "OpenAI Codex", get_codex_config_path, update_codex_config),
    ]
    for enabled, name, get_path, update_config in clients:
        if not enabled:
            continue
        config_path = get_path()
        if not config_path:
            results.append(f"{name}: Config location unavailable.")
            failed = True
            continue
        try:
            update_config(Path(config_path), server_entry)
            results.append(f"{name}: Registered {SERVER_NAME}.")
        except (OSError, ValueError, TypeError, ImportError) as error:
            results.append(f"{name}: Could not update {config_path}\n{error}")
            failed = True
    if any((enable_antigravity, enable_claude, enable_codex)):
        results.append("Fully quit and reopen each configured client to load the server.")
    return "\n\n".join(results), failed


def run_terminal_setup():
    print("SheetLink-MCP terminal setup")
    sheet_url = input("Google Apps Script Web App URL: ").strip()
    if not sheet_url:
        print("A Web App URL is required.")
        return 1
    success, message = test_url_connection(sheet_url)
    print(message)
    if not success and input("Save this URL anyway? [y/N] ").strip().lower() != "y":
        return 1
    selected = [
        input(f"Register in {name}? [Y/n] ").strip().lower() in ("", "y", "yes")
        for name in ("Google Antigravity", "Claude Desktop", "OpenAI Codex")
    ]
    try:
        summary, failed = install_configuration(sheet_url, *selected)
    except OSError as error:
        print(f"Could not save setup: {error}")
        return 1
    print(summary)
    return int(failed)


if __name__ == "__main__":
    if "--terminal" in sys.argv[1:]:
        sys.exit(run_terminal_setup())

    from browser_setup import run_browser_setup

    run_browser_setup(CONFIG_PATH, test_url_connection, install_configuration)
