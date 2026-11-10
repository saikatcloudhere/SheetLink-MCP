"""Local browser UI for setup, including systems without Tkinter."""

from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from secrets import token_urlsafe
from urllib.parse import parse_qs, urlsplit
import json
import webbrowser


CLIENTS = (
    ("antigravity", "Google Antigravity", "https://antigravity.google/download"),
    ("claude", "Claude Desktop", "https://claude.com/download"),
    ("codex", "OpenAI Codex", "https://openai.com/codex/"),
)


def is_web_app_url(url):
    parsed = urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.netloc == "script.google.com"
        and parsed.path.startswith(("/macros/s/", "/a/macros/"))
        and parsed.path.endswith("/exec")
        and not parsed.query
        and not parsed.fragment
    )


def render_page(path, sheet_url, selected, message="", done=False):
    icons = {"antigravity": "A", "claude": "✳", "codex": "&gt;_"}
    clients = "".join(
        f'<div class="client"><label><span class="app-icon {key}" aria-hidden="true">{icons[key]}</span>'
        f'<span>{name}</span><input type="checkbox" name="{key}"'
        f'{" checked" if key in selected else ""}></label>'
        f'<a href="{download}" target="_blank" rel="noreferrer" aria-label="Get {name}">Get app ↗</a></div>'
        for key, name, download in CLIENTS
    )
    status = f'<p class="status" role="status">{escape(message)}</p>' if message else ""
    body = f"""
    <section class="success">
      <span class="step" aria-hidden="true">✓</span>
      <h2>Connection complete</h2>
      {status}
      <p>Reopen the AI apps you connected to start using SheetLink.</p>
    </section>
    """ if done else f"""
    {status}
    <form action="{path}" method="post">
      <section aria-labelledby="apps-title">
        <header class="section-heading"><span class="step">01</span><h2 id="apps-title">Choose your AI apps</h2></header>
        <p class="muted">Open each app once after installing it, then fully quit it before connecting.</p>
        <div class="clients">{clients}</div>
      </section>
      <section aria-labelledby="sheet-title">
        <header class="section-heading"><span class="step">02</span><h2 id="sheet-title">Connect a Google Sheet</h2></header>
        <p class="muted">Use the Web App URL from your Google Apps Script deployment.</p>
        <label class="field-label" for="sheet-url">Web App URL</label>
        <input id="sheet-url" name="sheet_url" type="url" placeholder="https://script.google.com/…/exec"
               value="{escape(sheet_url, quote=True)}" required>
        <details{" open" if not sheet_url else ""}>
          <summary>Where do I find my Web App URL?</summary>
          <ol>
            <li><a href="https://sheets.new" target="_blank" rel="noreferrer">Open a blank Google Sheet</a>
                and choose <strong>Extensions → Apps Script</strong>.</li>
            <li><button type="button" id="copy">Copy the ready-made script</button>
                <span id="copy-status" role="status"></span>
                Paste it in place of the starter text in Apps Script, then save.</li>
            <li>Choose <strong>Deploy → New deployment → Web app</strong>.
                Set <strong>Execute as</strong> to <strong>Me</strong> and
                <strong>Who has access</strong> to <strong>Anyone</strong>.</li>
            <li>Click <strong>Deploy</strong>, approve access in Google, then copy the Web App URL.</li>
          </ol>
          <p class="notice">Use a test sheet first. Anyone with the deployed URL can read or edit data through this script.</p>
        </details>
      </section>
      <div class="actions"><button type="submit">Connect and finish <span aria-hidden="true">→</span></button></div>
    </form>
    <script>
      document.querySelector('#copy').addEventListener('click', async () => {{
        const status = document.querySelector('#copy-status');
        try {{
          const response = await fetch('{path}/script');
          if (!response.ok) throw new Error();
          await navigator.clipboard.writeText(await response.text());
          status.textContent = 'Copied.';
        }} catch {{
          status.innerHTML = 'Clipboard unavailable. <a href="{path}/script" target="_blank">Open the script</a> to copy it.';
        }}
      }});
    </script>
    """
    title = "You’re all set." if done else "Connect your first sheet."
    description = (
        "SheetLink is ready in your selected apps."
        if done else "Bring Google Sheets into the AI apps you already use."
    )
    return f"""<!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>SheetLink MCP · Setup</title>
      <style>
        :root {{
          color-scheme: dark;
          --ink: #f3f7f5; --muted: #aabbb4; --mint: #a7f3d0; --line: #2d413a;
          font: 16px/1.55 system-ui, sans-serif;
        }}
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0; min-height: 100vh; color: var(--ink);
          background: radial-gradient(ellipse 54rem 37rem at 77% -6%, #173a2f, transparent), #0a1210;
        }}
        .shell {{ width: min(100% - 2.5rem, 62rem); margin-inline: auto; }}
        .top, footer, .actions {{ display: flex; align-items: center; justify-content: space-between; gap: 1rem; }}
        .top {{ padding-block: 1.35rem; border-bottom: 1px solid var(--line); }}
        .brand, .github, .section-heading, .client label {{ display: flex; align-items: center; gap: .7rem; }}
        .brand {{ font-weight: 750; }}
        .logo, .step, .app-icon {{ display: inline-grid; flex: none; place-items: center; }}
        .logo {{ width: 2.1rem; height: 2.1rem; background: var(--mint); color: #10241c; border-radius: .65rem; }}
        .github {{
          padding: .45rem .75rem; border: 1px solid var(--line); border-radius: .6rem;
          color: var(--ink); text-decoration: none; font-size: .875rem;
        }}
        .hero {{ padding-block: clamp(2.25rem, 6vw, 4rem) 2rem; }}
        .eyebrow {{ color: var(--mint); font: 700 .72rem/1.5 system-ui; letter-spacing: .17em; text-transform: uppercase; }}
        h1 {{ font-size: clamp(2.35rem, 6vw, 4.35rem); line-height: 1.05; letter-spacing: -.065em; margin: .55rem 0 .8rem; }}
        h2 {{ font-size: 1.2rem; line-height: 1.25; margin: 0; letter-spacing: -.025em; }}
        p {{ margin: 0; }}
        .hero p:last-child, .muted, footer {{ color: var(--muted); }}
        .hero p:last-child {{ font-size: 1.05rem; }}
        form {{ display: grid; grid-template-columns: 1fr 1.24fr; align-items: start; gap: 1rem; }}
        section, .status {{
          background: #14221e; border: 1px solid var(--line); border-radius: 1rem;
          padding: clamp(1rem, 3vw, 1.5rem); box-shadow: 0 12px 32px #0002;
        }}
        .step {{
          width: 2rem; height: 2rem; border-radius: .55rem; background: #214036;
          color: var(--mint); font: 700 .75rem ui-monospace, monospace;
        }}
        .muted {{ font-size: .9rem; margin: .65rem 0 1.1rem; }}
        .clients {{ display: grid; gap: .5rem; }}
        .client {{ display: flex; align-items: center; gap: .65rem; border: 1px solid var(--line); border-radius: .65rem; padding-inline-end: .65rem; }}
        .client:has(input:checked) {{ border-color: #78c4a5; background: #1b352c; }}
        .client label {{ flex: 1; min-width: 0; padding: .55rem; cursor: pointer; font-size: .86rem; font-weight: 650; }}
        .client input {{ accent-color: var(--mint); inline-size: 1.05rem; block-size: 1.05rem; margin: 0 0 0 auto; flex: none; }}
        .client a {{ font-size: .74rem; flex: none; }}
        .app-icon {{ width: 1.9rem; height: 1.9rem; border-radius: .45rem; background: #31304d; color: #e2ddff; }}
        .claude {{ color: #ffd9c7; background: #503325; }}
        .codex {{ color: var(--mint); background: #233c35; font-family: ui-monospace, monospace; }}
        a {{ color: var(--mint); text-underline-offset: .2em; }}
        .field-label {{ display: block; font-size: .83rem; font-weight: 700; margin-bottom: .35rem; }}
        input[type=url] {{
          width: 100%; padding: .7rem .8rem; border: 1px solid #42584f; border-radius: .55rem;
          background: #0d1915; color: var(--ink); font: inherit; font-size: .9rem;
        }}
        input::placeholder {{ color: var(--muted); opacity: 1; }}
        details {{ border-top: 1px solid var(--line); margin-top: 1rem; padding-top: .75rem; font-size: .86rem; }}
        summary {{ cursor: pointer; font-weight: 700; color: var(--mint); }}
        ol {{ padding-inline-start: 1.3rem; }}
        li {{ margin-block: .55rem; padding-inline-start: .15rem; }}
        .notice {{ background: #342a18; color: #ffe3a5; border-radius: .5rem; padding: .65rem .8rem; }}
        button {{ font: inherit; cursor: pointer; }}
        #copy {{ color: var(--mint); background: #213b31; border: 1px solid #46675a; border-radius: .35rem; padding: .15rem .45rem; }}
        .actions {{ grid-column: 1 / -1; justify-content: flex-end; }}
        button[type=submit] {{
          display: flex; justify-content: space-between; gap: 1.5rem; padding: .8rem 1rem; border: 0;
          border-radius: .65rem; background: var(--mint); color: #10241c; font-weight: 750;
        }}
        button[type=submit]:hover {{ background: #c4fbe3; }}
        a:hover {{ color: #e1fff1; }}
        :focus-visible {{ outline: 2px solid var(--mint); outline-offset: 3px; }}
        .status {{ white-space: pre-wrap; margin-bottom: 1rem; border-color: #9a7941; }}
        .success {{ max-width: 39rem; }}
        .success h2 {{ margin: .7rem 0; }}
        .success .status {{ border: 0; padding: 0; box-shadow: none; color: var(--mint); }}
        footer {{ margin-block: 2rem; padding-block: 1rem; border-top: 1px solid var(--line); font-size: .8rem; }}
        @media (max-width: 47rem) {{
          form {{ grid-template-columns: minmax(0, 1fr); }}
          button[type=submit] {{ width: 100%; }}
        }}
      </style>
    </head>
    <body class="shell">
      <header class="top">
        <span class="brand"><span class="logo" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <rect x="4" y="4" width="16" height="16" rx="3"/><path d="M4 9h16M10 9v11M4 14h16"/>
          </svg>
        </span>SheetLink MCP</span>
        <a class="github" href="https://github.com/saikatcloudhere" target="_blank" rel="noreferrer">GitHub <span aria-hidden="true">↗</span></a>
      </header>
      <main>
        <div class="hero"><p class="eyebrow">SheetLink / Setup</p><h1>{title}</h1><p>{description}</p></div>
        {body}
      </main>
      <footer><span>Local setup wizard</span><a href="https://github.com/saikatcloudhere/SheetLink-MCP" target="_blank" rel="noreferrer">Project on GitHub ↗</a></footer>
    </body>
    </html>"""


def run_browser_setup(config_path, test_connection, install_configuration):
    script_path = Path(__file__).with_name("google_apps_script.js")
    try:
        saved_url = json.loads(Path(config_path).read_text(encoding="utf-8")).get("sheet_url", "")
        if not isinstance(saved_url, str):
            saved_url = ""
    except (OSError, ValueError, AttributeError):
        saved_url = ""
    path = "/" + token_urlsafe(24)
    finished = False

    class SetupHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def reply(self, status, content, kind="text/html"):
            data = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", f"{kind}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == path:
                self.reply(200, render_page(path, saved_url, ()))
            elif self.path == path + "/script":
                try:
                    self.reply(200, script_path.read_text(encoding="utf-8"), "text/plain")
                except OSError:
                    self.reply(404, "Script file is missing. Extract the full setup ZIP.", "text/plain")
            else:
                self.send_error(404)

        def do_POST(self):
            nonlocal finished
            if self.path != path:
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 8192:
                    raise ValueError
                fields = parse_qs(self.rfile.read(length).decode("utf-8"))
                sheet_url = fields.get("sheet_url", [""])[0].strip()
                valid_url = is_web_app_url(sheet_url)
            except ValueError:
                self.send_error(400)
                return
            selected = {key for key, _, _ in CLIENTS if key in fields}
            if not selected:
                message = "Select at least one AI app to connect."
            elif not valid_url:
                message = "Paste the Google Apps Script Web App URL ending in /exec."
            else:
                success, message = test_connection(sheet_url)
                if success:
                    try:
                        summary, failed = install_configuration(
                            sheet_url, *(key in selected for key, _, _ in CLIENTS)
                        )
                        message = summary
                        finished = not failed
                    except OSError as error:
                        message = f"Could not save setup. {error}"
            self.reply(200, render_page(path, sheet_url, selected, message, finished))

    with HTTPServer(("127.0.0.1", 0), SetupHandler) as server:
        url = f"http://127.0.0.1:{server.server_port}{path}"
        print(f"Open this address in your browser if setup does not open automatically:\n{url}", flush=True)
        webbrowser.open(url)
        while not finished:
            server.handle_request()
