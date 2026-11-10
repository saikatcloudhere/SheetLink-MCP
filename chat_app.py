"""
SheetLink-MCP: Standalone Visual Dashboard & Sheet Manager
Author: Saikat (https://github.com/saikatcloudhere)
Repository: https://github.com/saikatcloudhere/SheetLink-MCP

Zero-dependency graphical manager for users without Claude Desktop.
Allows reading, appending, searching, and managing Google Sheets in real-time.
"""

import os
import sys
import json
import requests
import webbrowser
import tkinter as tk
from tkinter import messagebox, ttk

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
AUTHOR_URL = "https://github.com/saikatcloudhere"


def get_sheet_url() -> str:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("sheet_url", "").strip()
        except Exception:
            pass
    return os.getenv("GOOGLE_SHEET_WEBAPP_URL", "").strip()


class SheetLinkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 SheetLink-MCP - Standalone Sheet Manager")
        self.root.geometry("820x640")
        self.root.minsize(700, 500)
        self.root.configure(bg="#0b1120")

        self.url = get_sheet_url()
        if not self.url:
            messagebox.showerror(
                "Configuration Missing",
                "Google Sheet URL not found in config.json.\nPlease run RUN_SETUP.bat first!"
            )
            sys.exit(1)

        self.setup_ui()
        self.load_sheet_data()

    def setup_ui(self):
        # 1. Header Card
        header = tk.Frame(self.root, bg="#1e293b", pady=12, padx=20)
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text="📊 SheetLink-MCP Live Manager",
            font=("Segoe UI", 15, "bold"),
            bg="#1e293b",
            fg="#f8fafc"
        )
        title.pack(side=tk.LEFT)

        author_btn = tk.Label(
            header,
            text="by Saikat (GitHub)",
            font=("Segoe UI", 9, "underline"),
            bg="#1e293b",
            fg="#38bdf8",
            cursor="hand2"
        )
        author_btn.pack(side=tk.RIGHT)
        author_btn.bind("<Button-1>", lambda e: webbrowser.open_new_tab(AUTHOR_URL))

        # 2. Main Content Frame
        main_frame = tk.Frame(self.root, bg="#0b1120", padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Action Bar (Add & Search)
        action_bar = tk.LabelFrame(
            main_frame,
            text=" ➕ Add New Row to Google Sheet ",
            font=("Segoe UI", 9, "bold"),
            bg="#0b1120",
            fg="#38bdf8",
            padx=15,
            pady=10
        )
        action_bar.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            action_bar,
            text="Enter values (comma-separated, e.g. Name, Phone, Area, Amount, Status):",
            font=("Segoe UI", 8),
            bg="#0b1120",
            fg="#94a3b8"
        ).pack(anchor="w")

        input_frame = tk.Frame(action_bar, bg="#0b1120")
        input_frame.pack(fill=tk.X, pady=(6, 0))

        self.row_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 10),
            bg="#1e293b",
            fg="#f8fafc",
            relief=tk.FLAT,
            insertbackground="#38bdf8"
        )
        self.row_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 10))
        self.row_entry.bind("<Return>", lambda e: self.add_row())

        self.add_btn = tk.Button(
            input_frame,
            text="➕ Append Row",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            command=self.add_row
        )
        self.add_btn.pack(side=tk.RIGHT)

        # Search Bar & Refresh Frame
        search_frame = tk.Frame(main_frame, bg="#0b1120")
        search_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            search_frame,
            text="🔍 Search:",
            font=("Segoe UI", 9, "bold"),
            bg="#0b1120",
            fg="#e2e8f0"
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.search_entry = tk.Entry(
            search_frame,
            font=("Segoe UI", 9),
            bg="#1e293b",
            fg="#f8fafc",
            relief=tk.FLAT,
            insertbackground="#38bdf8",
            width=25
        )
        self.search_entry.pack(side=tk.LEFT, ipady=4, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_table())

        self.refresh_btn = tk.Button(
            search_frame,
            text="🔄 Refresh Sheet",
            font=("Segoe UI", 9),
            bg="#334155",
            fg="#f8fafc",
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            command=self.load_sheet_data
        )
        self.refresh_btn.pack(side=tk.RIGHT)

        # 3. Live Sheet Table
        table_container = tk.Frame(main_frame, bg="#1e293b")
        table_container.pack(fill=tk.BOTH, expand=True)

        self.tree_scroll_y = tk.Scrollbar(table_container, orient=tk.VERTICAL)
        self.tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_scroll_x = tk.Scrollbar(table_container, orient=tk.HORIZONTAL)
        self.tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree = ttk.Treeview(
            table_container,
            yscrollcommand=self.tree_scroll_y.set,
            xscrollcommand=self.tree_scroll_x.set,
            selectmode="browse"
        )
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        # Configure style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#0f172a",
            foreground="#f8fafc",
            fieldbackground="#0f172a",
            rowheight=26,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Treeview.Heading",
            background="#1e293b",
            foreground="#38bdf8",
            font=("Segoe UI", 9, "bold")
        )
        style.map("Treeview", background=[("selected", "#2563eb")])

        # 4. Status Bar
        self.status_bar = tk.Label(
            self.root,
            text="Connecting to Google Sheet...",
            font=("Segoe UI", 8),
            bg="#1e293b",
            fg="#94a3b8",
            anchor="w",
            padx=15,
            pady=6
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.raw_data = []

    def load_sheet_data(self):
        self.status_bar.config(text="Fetching live data from Google Sheet...", fg="#38bdf8")
        self.root.update()

        try:
            res = requests.get(self.url, timeout=12, allow_redirects=True)
            res.raise_for_status()
            data = res.json()

            if data.get("status") == "success":
                rows = data.get("data", [])
                sheet_name = data.get("sheet_name", "Sheet1")
                self.raw_data = rows

                self.populate_table(rows)
                self.status_bar.config(
                    text=f"✅ Live connected to '{sheet_name}'. Total rows: {len(rows)}.",
                    fg="#4ade80"
                )
            else:
                self.status_bar.config(text=f"❌ Error: {data.get('message')}", fg="#f87171")
        except Exception as e:
            self.status_bar.config(text=f"❌ Network error: {str(e)}", fg="#f87171")

    def populate_table(self, rows):
        # Clear existing
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = []

        if not rows:
            self.tree["columns"] = ["Notice"]
            self.tree.heading("Notice", text="Status")
            self.tree.insert("", tk.END, values=["Sheet is completely empty."])
            return

        headers = [str(col) if str(col).strip() else f"Col {i+1}" for i, col in enumerate(rows[0])]
        self.tree["columns"] = headers
        self.tree["show"] = "headings"

        for h in headers:
            self.tree.heading(h, text=h)
            self.tree.column(h, width=140, minwidth=80)

        # Insert data rows (excluding header)
        for row in rows[1:]:
            padded_row = [str(item) for item in row] + [""] * (len(headers) - len(row))
            self.tree.insert("", tk.END, values=padded_row)

    def filter_table(self):
        query = self.search_entry.get().strip().lower()
        if not self.raw_data:
            return

        if not query:
            self.populate_table(self.raw_data)
            return

        headers = self.raw_data[0]
        filtered_rows = [headers]

        for row in self.raw_data[1:]:
            row_text = " ".join(str(cell) for cell in row).lower()
            if query in row_text:
                filtered_rows.append(row)

        self.populate_table(filtered_rows)

    def add_row(self):
        val_text = self.row_entry.get().strip()
        if not val_text:
            messagebox.showinfo("Input Required", "Please enter row values to append.")
            return

        row_values = [v.strip() for v in val_text.split(",") if v.strip()]
        if not row_values:
            return

        self.status_bar.config(text="Appending row to Google Sheet...", fg="#38bdf8")
        self.add_btn.config(state=tk.DISABLED)
        self.root.update()

        try:
            payload = {
                "action": "append_row",
                "row_data": row_values
            }
            res = requests.post(self.url, json=payload, timeout=12, allow_redirects=True)
            res.raise_for_status()
            data = res.json()

            if data.get("status") == "success":
                self.row_entry.delete(0, tk.END)
                self.load_sheet_data()
                messagebox.showinfo("Success", "✅ Row added to your Google Sheet successfully!")
            else:
                messagebox.showerror("Failed", f"Could not append row: {data.get('message')}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {str(e)}")
        finally:
            self.add_btn.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = SheetLinkApp(root)
    root.mainloop()
