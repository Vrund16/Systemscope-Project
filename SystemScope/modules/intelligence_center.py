"""SystemScope Intelligence Center: local performance black box and diagnostics.

This module only observes and records metrics. It does not kill processes, modify
startup settings, change system configuration, or delete files.
"""
from __future__ import annotations
import csv
import json
import math
import os
import platform
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import Canvas, filedialog, messagebox
import customtkinter as ctk
import psutil

BG = "#0b1020"
PANEL = "#111c2f"
BORDER = "#24334d"
MUTED = "#94a3b8"
WHITE = "#f8fafc"
BLUE = "#7c9cff"
GREEN = "#34d399"
AMBER = "#fbbf24"
RED = "#f87171"


def data_dir() -> Path:
    p = Path(__file__).resolve().parent.parent / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p


def fmt_bytes(n: int | float) -> str:
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} TB"


class IntelligenceCenter(ctk.CTkFrame):
    SAMPLE_SECONDS = 5

    def __init__(self, master):
        super().__init__(master, fg_color=BG)
        self.db_path = data_dir() / "intelligence_history.db"
        self.alive = True
        self.job = None
        self.last_sample = None
        self.storage_busy = False
        self.visual_mode = None
        self.visual_phase = 0.0
        self.visual_job = None
        self.visual_canvas = None
        self.visual_frame = None
        self.storage_snapshot = data_dir() / "storage_baseline.json"
        self._init_db()
        psutil.cpu_percent(None)
        self._build_ui()
        self.sample()
        self.protocol_bind = self.bind("<Destroy>", self._on_destroy, add="+")

    def _init_db(self):
        with sqlite3.connect(self.db_path, timeout=5) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS samples(
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
                epoch REAL NOT NULL, cpu REAL NOT NULL, ram REAL NOT NULL,
                disk REAL NOT NULL, swap REAL NOT NULL, top_processes TEXT NOT NULL)""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_intel_epoch ON samples(epoch)")

    def _build_ui(self):
        ctk.CTkLabel(self, text="PC Intelligence Center", font=ctk.CTkFont(size=28, weight="bold"), text_color=WHITE).pack(anchor="w", padx=24, pady=(20, 3))
        ctk.CTkLabel(self, text="Performance black box · health score · trend diagnosis · network and storage investigations", text_color=MUTED).pack(anchor="w", padx=26, pady=(0, 14))

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", padx=18)
        self.metric = {}
        for i, (name, accent, hint) in enumerate([
            ("PC HEALTH", BLUE, "Evidence-based estimate"), ("CPU LOAD", GREEN, "Current utilization"),
            ("MEMORY", AMBER, "RAM currently used"), ("SYSTEM DISK", RED, "Space currently used")]):
            cards.grid_columnconfigure(i, weight=1, uniform="metric")
            card = ctk.CTkFrame(cards, fg_color=PANEL, corner_radius=13, border_width=1, border_color=BORDER)
            card.grid(row=0, column=i, sticky="ew", padx=5, pady=3)
            ctk.CTkLabel(card, text=name, text_color=MUTED, font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=13, pady=(12, 3))
            value = ctk.CTkLabel(card, text="—", text_color=accent, font=ctk.CTkFont(size=25, weight="bold"))
            value.pack(anchor="w", padx=13, pady=(0, 1))
            ctk.CTkLabel(card, text=hint, text_color=MUTED, font=ctk.CTkFont(size=10)).pack(anchor="w", padx=13, pady=(0, 12))
            self.metric[name] = value

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=24, pady=(14, 6))
        ctk.CTkButton(toolbar, text="Refresh Now", command=self.sample, width=110).pack(side="left", padx=(0, 7))
        ctk.CTkButton(toolbar, text="Network App Detective", command=self.network_scan, fg_color="#26354f", hover_color="#344867").pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Storage Change Radar", command=self.storage_radar, fg_color="#26354f", hover_color="#344867").pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Export Diagnostic Report", command=self.export_report, fg_color="#26354f", hover_color="#344867").pack(side="left", padx=4)

        self.status = ctk.CTkLabel(self, text=f"Black box sampling every {self.SAMPLE_SECONDS}s · saved locally · no automatic changes", text_color=MUTED, anchor="w")
        self.status.pack(fill="x", padx=27, pady=(2, 7))
        # Animated investigation panel is shown only for Network or Storage tools.
        self.visual_frame = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=13, border_width=1, border_color=BORDER)
        self.visual_canvas = Canvas(self.visual_frame, height=190, bg=PANEL, bd=0, highlightthickness=0)
        self.visual_canvas.pack(fill="x", expand=False, padx=6, pady=6)
        self.visual_frame.pack_forget()
        self.output = ctk.CTkTextbox(self, fg_color=PANEL, text_color="#dbeafe", font=ctk.CTkFont(family="Consolas", size=11), corner_radius=13)
        self.output.pack(fill="both", expand=True, padx=24, pady=(0, 18))
        self._write("SYSTEMSCOPE PC INTELLIGENCE CENTER\n" + "=" * 78 + "\n\nCollecting first sample…\n\n" +
                    "WHAT THIS PAGE DOES\n• Saves resource trends locally to help investigate slowdowns.\n" +
                    "• Estimates a transparent health score from current CPU/RAM/disk pressure.\n" +
                    "• Can inspect current network connections and compare a chosen folder against a saved storage baseline.\n\n" +
                    "LIMITATIONS\n• A high score is not a guarantee of system health; it is a simple heuristic.\n" +
                    "• Network connections are not a malware verdict. Storage radar scans only the folder you select.\n")

    def _write(self, text):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("end", text)
        self.output.configure(state="normal")

    def _get_metrics(self):
        cpu = float(psutil.cpu_percent(interval=0.25))
        ram = float(psutil.virtual_memory().percent)
        swap = float(psutil.swap_memory().percent)
        drive = os.environ.get("SystemDrive", "C:") + "\\" if os.name == "nt" else "/"
        try:
            disk = float(psutil.disk_usage(drive).percent)
        except (OSError, ValueError):
            disk = 0.0
        # Keep the process snapshot deliberately small to limit background overhead.
        top = []
        for proc in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                info = proc.info
                mem = info.get("memory_info")
                if mem:
                    top.append({"pid": info.get("pid"), "name": info.get("name") or "Unknown", "rss": int(mem.rss)})
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess, OSError):
                continue
        top.sort(key=lambda x: x["rss"], reverse=True)
        return cpu, ram, disk, swap, top[:8]

    @staticmethod
    def _health_score(cpu, ram, disk, swap):
        # Transparent pressure score, not a diagnosis or benchmark.
        score = round(max(0, 100 - (max(0, cpu - 35) * 0.35) - (max(0, ram - 50) * 0.65)
                          - (max(0, disk - 80) * 0.5) - (max(0, swap - 30) * 0.25)))
        return max(0, min(100, score))

    def sample(self):
        if not self.alive or not self.winfo_exists():
            return
        try:
            cpu, ram, disk, swap, top = self._get_metrics()
            now = datetime.now().astimezone()
            epoch = time.time()
            with sqlite3.connect(self.db_path, timeout=5) as db:
                db.execute("INSERT INTO samples(timestamp,epoch,cpu,ram,disk,swap,top_processes) VALUES(?,?,?,?,?,?,?)",
                           (now.isoformat(timespec="seconds"), epoch, cpu, ram, disk, swap, json.dumps(top)))
                db.execute("DELETE FROM samples WHERE epoch < ?", (epoch - 60 * 60 * 24 * 30,))
            score = self._health_score(cpu, ram, disk, swap)
            self.metric["PC HEALTH"].configure(text=f"{score}/100")
            self.metric["CPU LOAD"].configure(text=f"{cpu:.1f}%")
            self.metric["MEMORY"].configure(text=f"{ram:.1f}%")
            self.metric["SYSTEM DISK"].configure(text=f"{disk:.1f}%")
            lines = ["PERFORMANCE BLACK BOX · LATEST SNAPSHOT", "=" * 78,
                     f"Captured: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}", f"CPU sample window: 0.25 seconds | PC health heuristic: {score}/100",
                     f"CPU {cpu:.1f}% | RAM {ram:.1f}% | System disk {disk:.1f}% | Swap {swap:.1f}%", ""]
            lines += self._recommendations(cpu, ram, disk, swap)
            lines += ["", "TOP MEMORY PROCESSES (snapshot only)", "-" * 78]
            lines += [f"PID {p['pid']!s:<8} {fmt_bytes(p['rss']):>10}   {p['name']}" for p in top] or ["Process details unavailable."]
            with sqlite3.connect(self.db_path, timeout=5) as db:
                recent = db.execute("SELECT timestamp,cpu,ram,disk FROM samples ORDER BY id DESC LIMIT 6").fetchall()
                total = db.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
            lines += ["", "RECENT BLACK-BOX TREND (newest first)", "-" * 78]
            lines += [f"{ts} | CPU {c:5.1f}% | RAM {r:5.1f}% | Disk {d:5.1f}%" for ts,c,r,d in recent]
            lines += ["", f"Saved samples: {total:,} · Retention: 30 days · Database: {self.db_path.name}",
                      "Score is a simple pressure heuristic, not a medical-grade diagnosis of the PC."]
            self._write("\n".join(lines))
            self.status.configure(text=f"Last sample {now.strftime('%H:%M:%S')} · {total:,} samples stored locally · next in {self.SAMPLE_SECONDS}s")
        except (OSError, sqlite3.Error, RuntimeError) as exc:
            self.status.configure(text=f"Sampling issue: {exc}")
        if self.alive and self.winfo_exists():
            self.job = self.after(self.SAMPLE_SECONDS * 1000, self.sample)

    @staticmethod
    def _recommendations(cpu, ram, disk, swap):
        out = ["QUICK DIAGNOSIS & SAFE NEXT STEPS", "-" * 78]
        flags = 0
        if cpu >= 85:
            out += ["[HIGH] CPU pressure is elevated. Sort System Monitor by CPU and inspect the process while the issue is happening."]
            flags += 1
        if ram >= 85:
            out += ["[HIGH] Memory pressure is elevated. Check top memory processes and close apps you recognize but do not need."]
            flags += 1
        if disk >= 90:
            out += ["[HIGH] System drive is nearly full. Review Storage Intelligence results before removing anything."]
            flags += 1
        if swap >= 60:
            out += ["[WATCH] Swap/pagefile use is high. This can accompany memory pressure; compare RAM and process trends."]
            flags += 1
        if not flags:
            out.append("[OK] No configured high-pressure threshold is currently crossed. This does not rule out every problem.")
        out.append("No process is terminated and no system setting is changed by these recommendations.")
        return out


    def _start_visual(self, mode):
        """Start a lightweight Canvas animation for the selected investigation."""
        self.visual_mode = mode
        self.visual_phase = 0.0
        if self.visual_job is not None:
            try:
                self.after_cancel(self.visual_job)
            except Exception:
                pass
            self.visual_job = None
        self.visual_frame.pack(fill="x", padx=24, pady=(0, 8), before=self.output)
        self._animate_visual()

    def _animate_visual(self):
        if not self.alive or not self.winfo_exists() or self.visual_canvas is None or not self.visual_mode:
            return
        c = self.visual_canvas
        c.delete("all")
        width = max(c.winfo_width(), 620)
        height = 190
        c.configure(height=height)
        self.visual_phase = (self.visual_phase + 0.075) % (2 * math.pi)
        if self.visual_mode == "network":
            # Satellite-style orbit visualization (visual metaphor; not geolocation).
            cx, cy = width * 0.27, 91
            c.create_text(18, 15, anchor="w", text="NETWORK APP DETECTIVE  /  LIVE CONNECTION VIEW", fill="#7dd3fc", font=("Segoe UI", 10, "bold"))
            for rx, ry in ((62, 24), (100, 43), (143, 62)):
                c.create_oval(cx-rx, cy-ry, cx+rx, cy+ry, outline="#1f5270", width=1)
            c.create_oval(cx-22, cy-22, cx+22, cy+22, fill="#12324b", outline="#38bdf8", width=2)
            c.create_text(cx, cy, text="NET", fill="#e0f2fe", font=("Segoe UI", 9, "bold"))
            angle = self.visual_phase
            sx, sy = cx + 100 * math.cos(angle), cy + 43 * math.sin(angle)
            c.create_line(sx-12, sy, sx+12, sy, fill="#67e8f9", width=3)
            c.create_line(sx, sy-8, sx, sy+8, fill="#67e8f9", width=3)
            c.create_oval(sx-4, sy-4, sx+4, sy+4, fill="#e0f2fe", outline="")
            for i in range(7):
                a = angle + i * (2*math.pi/7)
                nx, ny = cx + 143 * math.cos(a), cy + 62 * math.sin(a)
                c.create_line(cx, cy, nx, ny, fill="#173a56", width=1)
                c.create_oval(nx-3, ny-3, nx+3, ny+3, fill="#22d3ee", outline="")
            c.create_text(width*0.53, 64, anchor="w", text="LOCAL SOCKET CONNECTIONS", fill="#e2e8f0", font=("Segoe UI", 12, "bold"))
            c.create_text(width*0.53, 91, anchor="w", text="Process · PID · State · Local / Remote address", fill="#94a3b8", font=("Segoe UI", 10))
            c.create_text(width*0.53, 119, anchor="w", text="Snapshot captured below · refresh by clicking Network App Detective", fill="#67e8f9", font=("Segoe UI", 9))
            c.create_text(width*0.53, 151, anchor="w", text="Orbit animation is decorative; no satellite tracking or packet interception.", fill="#64748b", font=("Segoe UI", 9))
        else:
            # Separate storage-platter animation with rotating scan beam.
            cx, cy = width * 0.27, 96
            c.create_text(18, 15, anchor="w", text="STORAGE CHANGE RADAR  /  FOLDER SCAN", fill="#86efac", font=("Segoe UI", 10, "bold"))
            for r in (24, 44, 64):
                c.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#245b4a", width=1)
            c.create_oval(cx-15, cy-15, cx+15, cy+15, fill="#14372f", outline="#34d399", width=2)
            c.create_text(cx, cy, text="SSD", fill="#d1fae5", font=("Segoe UI", 8, "bold"))
            a = self.visual_phase
            ex, ey = cx + 64*math.cos(a), cy + 64*math.sin(a)
            c.create_arc(cx-64, cy-64, cx+64, cy+64, start=-math.degrees(a), extent=-42, outline="#34d399", style="arc", width=4)
            c.create_line(cx, cy, ex, ey, fill="#6ee7b7", width=2)
            for i, (dx, dy) in enumerate(((90,-25),(125,18),(80,52),(155,-48),(170,42))):
                pulse = 3 + (2 if math.sin(a+i) > 0.65 else 0)
                c.create_rectangle(cx+dx, cy+dy, cx+dx+pulse*2, cy+dy+pulse*2, fill="#a7f3d0", outline="")
            c.create_text(width*0.53, 64, anchor="w", text="SCANNING FILE METADATA", fill="#e2e8f0", font=("Segoe UI", 12, "bold"))
            c.create_text(width*0.53, 91, anchor="w", text="Compare file paths, sizes and modification times", fill="#94a3b8", font=("Segoe UI", 10))
            c.create_text(width*0.53, 119, anchor="w", text="Added · Changed · Removed · Total size delta", fill="#86efac", font=("Segoe UI", 10, "bold"))
            c.create_text(width*0.53, 151, anchor="w", text="Decorative scan sweep · files are not changed or deleted.", fill="#64748b", font=("Segoe UI", 9))
        self.visual_job = self.after(45, self._animate_visual)

    def network_scan(self):
        self._start_visual("network")
        lines = ["NETWORK APP DETECTIVE", "=" * 78, f"Captured: {datetime.now().astimezone().isoformat(timespec='seconds')}",
                 "Current socket connections visible to this user. This is not a malware verdict.", ""]
        found = []
        try:
            for conn in psutil.net_connections(kind="inet"):
                try:
                    pid = conn.pid
                    procname = psutil.Process(pid).name() if pid else "PID unavailable / system-owned"
                    laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "—"
                    raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "—"
                    found.append((procname.lower(), pid or 0, procname, conn.status, laddr, raddr))
                except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess, OSError):
                    continue
        except (psutil.AccessDenied, OSError, NotImplementedError) as exc:
            lines += [f"Could not enumerate all connections: {exc}", "Try running normally first; elevated access may reveal more, but is not required by this app."]
        found.sort(key=lambda x: (x[0], x[1]))
        lines += [f"Connections visible: {len(found)}", "", "PROCESS / PID / STATE / LOCAL / REMOTE", "-" * 78]
        lines += [f"{name[:23]:23} PID {pid:<7} {state[:12]:12} {local:22} -> {remote}" for _,pid,name,state,local,remote in found[:250]]
        if len(found) > 250: lines.append(f"Showing first 250 of {len(found)} connections.")
        if not found: lines.append("No connections returned or access is restricted on this platform.")
        lines += ["", "Review unknown entries carefully. A connection alone does not imply malicious activity."]
        self._write("\n".join(lines))

    def storage_radar(self):
        if self.storage_busy:
            return
        self._start_visual("storage")
        folder = filedialog.askdirectory(parent=self.winfo_toplevel(), title="Choose a folder for Storage Change Radar")
        if not folder:
            return
        self.storage_busy = True
        self.status.configure(text="Storage radar scanning in background…")
        self._write(f"STORAGE CHANGE RADAR\n{'='*78}\nScanning selected folder:\n{folder}\n\nThis scan reads file metadata only. Please wait…")
        def worker():
            records = []
            count = 0
            total = 0
            errors = 0
            try:
                for root, dirs, files in os.walk(folder, onerror=lambda _e: None):
                    dirs[:] = [d for d in dirs if d not in {"$RECYCLE.BIN", "System Volume Information", "node_modules", ".git", "__pycache__"}]
                    for name in files:
                        p = os.path.join(root, name)
                        try:
                            st = os.stat(p, follow_symlinks=False)
                            if not os.path.isfile(p):
                                continue
                            count += 1; total += st.st_size
                            records.append({"path": os.path.relpath(p, folder), "size": st.st_size, "mtime": st.st_mtime})
                        except (OSError, PermissionError):
                            errors += 1
                baseline = {"folder": os.path.abspath(folder), "created": datetime.now().astimezone().isoformat(timespec="seconds"), "count": count, "total": total, "records": records}
                old = None
                if self.storage_snapshot.exists():
                    try:
                        candidate = json.loads(self.storage_snapshot.read_text(encoding="utf-8"))
                        if os.path.normcase(candidate.get("folder", "")) == os.path.normcase(os.path.abspath(folder)):
                            old = candidate
                    except (OSError, ValueError, TypeError):
                        old = None
                self.storage_snapshot.write_text(json.dumps(baseline), encoding="utf-8")
                result = {"baseline": baseline, "old": old, "errors": errors, "folder": folder}
                self.after(0, lambda r=result: self._show_storage_radar(r))
            except Exception as exc:
                self.after(0, lambda e=str(exc): self._storage_error(e))
        threading.Thread(target=worker, daemon=True).start()

    def _show_storage_radar(self, result):
        self.storage_busy = False
        if not self.winfo_exists(): return
        b, old = result["baseline"], result["old"]
        lines = ["STORAGE CHANGE RADAR", "=" * 78, f"Folder: {result['folder']}", f"Current scan: {b['created']}",
                 f"Files: {b['count']:,} | Combined size: {fmt_bytes(b['total'])}", f"Metadata errors/skips: {result['errors']}", ""]
        if old:
            previous = {r["path"]: r for r in old.get("records", [])}
            current = {r["path"]: r for r in b["records"]}
            added = [r for p,r in current.items() if p not in previous]
            removed = [r for p,r in previous.items() if p not in current]
            changed = [(current[p], previous[p]) for p in current.keys() & previous.keys() if current[p].get("size") != previous[p].get("size") or current[p].get("mtime") != previous[p].get("mtime")]
            delta = b["total"] - old.get("total", 0)
            lines += ["COMPARE WITH PREVIOUS BASELINE", "-" * 78, f"Previous scan: {old.get('created','unknown')}",
                      f"Total size change: {'+' if delta >= 0 else ''}{fmt_bytes(abs(delta))} ({'growth' if delta > 0 else 'shrinkage' if delta < 0 else 'no net size change'})",
                      f"Added files: {len(added)} | Removed files: {len(removed)} | Changed files: {len(changed)}", ""]
            lines += ["LARGEST NEW FILES", "-" * 78]
            lines += [f"{fmt_bytes(r['size']):>10}  {r['path']}" for r in sorted(added, key=lambda x:x['size'], reverse=True)[:40]] or ["No newly detected files."]
            lines += ["", "LARGEST CHANGED FILES", "-" * 78]
            lines += [f"{fmt_bytes(now['size']):>10}  {now['path']} (previous {fmt_bytes(prev['size'])})" for now,prev in sorted(changed, key=lambda x:abs(x[0]['size']-x[1]['size']), reverse=True)[:40]] or ["No changed file sizes/timestamps detected."]
            lines += ["", "REMOVED FILES (recorded only; no recovery or deletion action performed)", "-" * 78]
            lines += [f"{fmt_bytes(r['size']):>10}  {r['path']}" for r in sorted(removed, key=lambda x:x['size'], reverse=True)[:30]] or ["No removed files detected."]
        else:
            lines += ["A baseline has been saved. Run Storage Change Radar again on the same folder to compare changes.",
                      "Baseline is stored locally in data/storage_baseline.json."]
        lines += ["", "Safety: this feature compares metadata; it does not decide whether a file is safe to delete."]
        self._write("\n".join(lines))
        self.status.configure(text=f"Storage scan complete · {b['count']:,} files · baseline saved locally")

    def _storage_error(self, message):
        self.storage_busy = False
        if self.winfo_exists():
            self.status.configure(text=f"Storage scan failed: {message}")
            messagebox.showerror("Storage Change Radar", message, parent=self.winfo_toplevel())

    def export_report(self):
        path = filedialog.asksaveasfilename(parent=self.winfo_toplevel(), title="Save SystemScope diagnostic report", defaultextension=".html", filetypes=[("HTML report", "*.html"), ("CSV samples", "*.csv")], initialfile="systemscope_diagnostic_report.html")
        if not path: return
        try:
            with sqlite3.connect(self.db_path, timeout=5) as db:
                rows = db.execute("SELECT timestamp,cpu,ram,disk,swap,top_processes FROM samples ORDER BY id DESC LIMIT 2000").fetchall()
            if path.lower().endswith(".csv"):
                with open(path, "w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f); w.writerow(["timestamp", "cpu_percent", "ram_percent", "disk_percent", "swap_percent", "top_processes_json"]); w.writerows(reversed(rows))
            else:
                esc = lambda x: str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
                tr = "".join(f"<tr><td>{esc(ts)}</td><td>{cpu:.1f}%</td><td>{ram:.1f}%</td><td>{disk:.1f}%</td><td>{swap:.1f}%</td></tr>" for ts,cpu,ram,disk,swap,_ in rows[:500])
                avg = lambda i: sum(r[i] for r in rows) / len(rows) if rows else 0
                html = f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>SystemScope Diagnostic Report</title><style>body{{font:15px Segoe UI,Arial;max-width:1100px;margin:35px auto;padding:0 20px;background:#0b1020;color:#edf2ff}}h1{{color:#7c9cff}}.card,table{{background:#111c2f;border-radius:12px;padding:15px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #293650;text-align:left}}small{{color:#94a3b8}}</style></head><body><h1>SystemScope Diagnostic Report</h1><small>Generated {esc(datetime.now().astimezone().isoformat(timespec='seconds'))} · Local resource history</small><p class='card'>Samples: {len(rows)} · Average CPU: {avg(1):.1f}% · Average RAM: {avg(2):.1f}% · Average disk: {avg(3):.1f}%</p><h2>Recent history (up to 500 rows)</h2><table><tr><th>Timestamp</th><th>CPU</th><th>RAM</th><th>Disk</th><th>Swap</th></tr>{tr}</table><p><small>This report contains machine usage data and process names. Review it before sharing. Thresholds and health scores are heuristics, not a malware or hardware diagnosis.</small></p></body></html>"""
                Path(path).write_text(html, encoding="utf-8")
            messagebox.showinfo("Export complete", f"Diagnostic report saved to:\n{path}", parent=self.winfo_toplevel())
        except (OSError, sqlite3.Error) as exc:
            messagebox.showerror("Export failed", str(exc), parent=self.winfo_toplevel())

    def _on_destroy(self, _event=None):
        self.alive = False
        if self.job is not None:
            try: self.after_cancel(self.job)
            except Exception: pass
            self.job = None
        if self.visual_job is not None:
            try: self.after_cancel(self.visual_job)
            except Exception: pass
            self.visual_job = None
