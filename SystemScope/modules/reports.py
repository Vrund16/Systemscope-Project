"""Local resource-history reports for SystemScope."""
import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk
from modules.performance_doctor import app_data_dir

BG = "#0b1020"
PANEL = "#121a2d"
MUTED = "#9aa8bf"
WHITE = "#f4f7ff"
ACCENT = "#7c9cff"

class ReportsCenter(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG)
        self.db_path = app_data_dir() / "resource_history.db"
        ctk.CTkLabel(self, text="Resource Reports", font=ctk.CTkFont(size=28, weight="bold"), text_color=WHITE).pack(anchor="w", padx=24, pady=(22, 4))
        ctk.CTkLabel(self, text="Review locally saved monitoring history and export shareable reports.", text_color=MUTED).pack(anchor="w", padx=26, pady=(0, 18))
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", padx=20)
        self.metrics = {}
        for title in ("Samples saved", "Average CPU", "Average RAM"):
            card = ctk.CTkFrame(cards, fg_color=PANEL, corner_radius=14, border_width=1, border_color="#24304a")
            card.pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkLabel(card, text=title.upper(), text_color=MUTED, font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=14, pady=(14, 4))
            val = ctk.CTkLabel(card, text="—", text_color=ACCENT, font=ctk.CTkFont(size=25, weight="bold"))
            val.pack(anchor="w", padx=14, pady=(0, 14)); self.metrics[title] = val
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=24, pady=16)
        ctk.CTkButton(actions, text="Refresh report", command=self.refresh).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Export CSV", command=self.export_csv, fg_color="#26354f", hover_color="#344867").pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Export HTML report", command=self.export_html, fg_color="#26354f", hover_color="#344867").pack(side="left")
        self.output = ctk.CTkTextbox(self, fg_color=PANEL, text_color="#dce6fb", font=ctk.CTkFont(size=12), corner_radius=14)
        self.output.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        self.refresh()

    def _rows(self):
        if not self.db_path.exists(): return [], []
        with sqlite3.connect(self.db_path, timeout=3) as db:
            try: samples = db.execute("SELECT timestamp,cpu,ram,disk,top_processes FROM samples ORDER BY id DESC LIMIT 5000").fetchall()
            except sqlite3.Error: samples = []
            try: events = db.execute("SELECT timestamp,severity,category,message FROM events ORDER BY id DESC LIMIT 200").fetchall()
            except sqlite3.Error: events = []
        return samples, events

    def refresh(self):
        try: samples, events = self._rows()
        except sqlite3.Error as exc:
            self.output.delete("1.0", "end"); self.output.insert("end", f"Could not read local history: {exc}\n"); return
        self.metrics["Samples saved"].configure(text=f"{len(samples):,}")
        self.metrics["Average CPU"].configure(text=f"{sum(r[1] for r in samples)/len(samples):.1f}%" if samples else "—")
        self.metrics["Average RAM"].configure(text=f"{sum(r[2] for r in samples)/len(samples):.1f}%" if samples else "—")
        lines = ["SYSTEMSCOPE · LOCAL RESOURCE REPORT", "=" * 66, f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}", f"Database: {self.db_path}", "", "LATEST RESOURCE SAMPLES", "-" * 66]
        if samples:
            for timestamp, cpu, ram, disk, _ in samples[:30]: lines.append(f"{timestamp:<28} CPU {cpu:5.1f}%   RAM {ram:5.1f}%   Disk {disk:5.1f}%")
            lines.append(f"\nShowing latest {min(30, len(samples))} of {len(samples)} saved samples (up to 5,000 loaded).")
        else: lines.append("No saved samples yet. Open Performance Doctor and leave monitoring active for a few minutes.")
        lines += ["", "RECENT WARNINGS", "-" * 66]
        lines += [f"{ts} | {sev} | {cat}: {msg}" for ts, sev, cat, msg in events] or ["No warnings recorded."]
        self.output.delete("1.0", "end"); self.output.insert("end", "\n".join(lines))

    def export_csv(self):
        samples, _ = self._rows()
        path = filedialog.asksaveasfilename(parent=self.winfo_toplevel(), title="Export resource samples", defaultextension=".csv", filetypes=[("CSV file", "*.csv")], initialfile="systemscope_resource_history.csv")
        if not path: return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f); writer.writerow(["timestamp", "cpu_percent", "ram_percent", "disk_percent", "top_processes"]); writer.writerows(reversed(samples))
            messagebox.showinfo("Export complete", f"Saved {len(samples)} samples.\n{path}", parent=self.winfo_toplevel())
        except OSError as exc: messagebox.showerror("Export failed", str(exc), parent=self.winfo_toplevel())

    def export_html(self):
        samples, events = self._rows()
        path = filedialog.asksaveasfilename(parent=self.winfo_toplevel(), title="Export HTML report", defaultextension=".html", filetypes=[("HTML report", "*.html")], initialfile="systemscope_report.html")
        if not path: return
        esc = lambda value: str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        rows = "".join(f"<tr><td>{esc(ts)}</td><td>{cpu:.1f}%</td><td>{ram:.1f}%</td><td>{disk:.1f}%</td></tr>" for ts,cpu,ram,disk,_ in samples[:500])
        warnings = "".join(f"<li><b>{esc(ts)}</b> · {esc(sev)} · {esc(cat)}: {esc(msg)}</li>" for ts,sev,cat,msg in events)
        html = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>SystemScope Report</title><style>body{{font:15px Segoe UI,Arial;background:#0b1020;color:#edf2ff;max-width:1100px;margin:40px auto;padding:0 20px}}h1{{color:#8ba7ff}}.card,table{{background:#121a2d;border-radius:12px;padding:16px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:10px;border-bottom:1px solid #293650;text-align:left}}small{{color:#9aa8bf}}</style></head><body><h1>SystemScope Resource Report</h1><small>Generated {esc(datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'))} · Local data only</small><p class="card">Samples loaded: {len(samples)} · Average CPU: {(sum(r[1] for r in samples)/len(samples)) if samples else 0:.1f}% · Average RAM: {(sum(r[2] for r in samples)/len(samples)) if samples else 0:.1f}%</p><h2>Resource history (latest 500)</h2><table><thead><tr><th>Timestamp</th><th>CPU</th><th>RAM</th><th>Disk</th></tr></thead><tbody>{rows}</tbody></table><h2>Recent warnings</h2><ul>{warnings or '<li>No warnings recorded.</li>'}</ul><p><small>SystemScope uses threshold-based guidance, not a definitive hardware diagnosis.</small></p></body></html>'''
        try:
            Path(path).write_text(html, encoding="utf-8")
            messagebox.showinfo("Export complete", f"HTML report saved.\n{path}", parent=self.winfo_toplevel())
        except OSError as exc: messagebox.showerror("Export failed", str(exc), parent=self.winfo_toplevel())
