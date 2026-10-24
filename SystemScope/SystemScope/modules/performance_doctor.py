"""SystemScope Performance Doctor: rule-based diagnostics and SQLite history."""
from __future__ import annotations

import csv
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import psutil

BG = "#0b1120"
PANEL = "#111c2f"
BLUE = "#60a5fa"
GREEN = "#34d399"
AMBER = "#fbbf24"
RED = "#f87171"
MUTED = "#94a3b8"
WHITE = "#f8fafc"


def app_data_dir() -> Path:
    # Store app history alongside the project, not in a system folder.
    folder = Path(__file__).resolve().parent.parent / "data"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


class PerformanceDoctor(ctk.CTkFrame):
    """Monitors resource usage, records history, and offers conservative tips."""

    SAMPLE_SECONDS = 5
    CPU_LIMIT = 85.0
    RAM_LIMIT = 85.0
    DISK_LIMIT = 90.0

    def __init__(self, master):
        super().__init__(master, fg_color=BG)
        self.alive = True
        self.after_id = None
        self.db_path = app_data_dir() / "resource_history.db"
        self.last_alert_state = {"CPU": False, "RAM": False, "Disk": False}
        self._init_db()
        psutil.cpu_percent(interval=None)
        for proc in psutil.process_iter():
            try:
                proc.cpu_percent(None)
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                pass

        ctk.CTkLabel(self, text="Performance Doctor", font=ctk.CTkFont(size=28, weight="bold"), text_color=WHITE).pack(anchor="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(self, text="Rule-based diagnostics, process snapshots and persistent resource history", text_color=MUTED).pack(anchor="w", padx=26, pady=(0, 14))

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", padx=18)
        self.metric_labels = {}
        for name in ("CPU", "RAM", "Disk"):
            card = ctk.CTkFrame(cards, fg_color=PANEL, corner_radius=12)
            card.pack(side="left", fill="x", expand=True, padx=6)
            ctk.CTkLabel(card, text=name + " usage", text_color=MUTED).pack(anchor="w", padx=14, pady=(12, 2))
            value = ctk.CTkLabel(card, text="Collecting…", font=ctk.CTkFont(size=23, weight="bold"), text_color=WHITE)
            value.pack(anchor="w", padx=14, pady=(0, 12))
            self.metric_labels[name] = value

        self.diagnosis = ctk.CTkTextbox(self, height=145, fg_color=PANEL, text_color="#dbeafe", font=ctk.CTkFont(size=12))
        self.diagnosis.pack(fill="x", padx=24, pady=(14, 10))
        self.diagnosis.insert("end", "Starting monitoring…\n")
        self.diagnosis.configure(state="disabled")

        ctk.CTkLabel(self, text="Recent warnings and process snapshots", font=ctk.CTkFont(size=16, weight="bold"), text_color=WHITE).pack(anchor="w", padx=25, pady=(3, 5))
        self.events = ctk.CTkTextbox(self, fg_color=PANEL, text_color="#dbeafe", font=("Consolas", 11))
        self.events.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=24, pady=(0, 16))
        ctk.CTkButton(bottom, text="Export History to CSV", command=self.export_csv).pack(side="left")
        ctk.CTkButton(bottom, text="Refresh Now", fg_color="#334155", hover_color="#475569", command=self.sample).pack(side="left", padx=8)
        ctk.CTkLabel(bottom, text=f"Saved locally: {self.db_path.name} · samples every {self.SAMPLE_SECONDS}s", text_color=MUTED).pack(side="right")
        self.load_recent_events()
        self.after_id = self.after(700, self.sample)

    def _connect(self):
        connection = sqlite3.connect(self.db_path, timeout=5)
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _init_db(self):
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cpu REAL NOT NULL,
                ram REAL NOT NULL,
                disk REAL NOT NULL,
                top_processes TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                severity TEXT NOT NULL,
                category TEXT NOT NULL,
                message TEXT NOT NULL,
                process_snapshot TEXT NOT NULL
            )""")

    @staticmethod
    def _disk_percent():
        try:
            drive = (os.environ.get("SystemDrive", "C:") + "\\") if os.name == "nt" else "/"
            return psutil.disk_usage(drive).percent
        except (OSError, ValueError):
            try:
                return psutil.disk_usage("C:\\").percent
            except (OSError, ValueError):
                return 0.0

    @staticmethod
    def _process_snapshot():
        items = []
        for proc in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
            try:
                info = proc.info
                items.append((float(info.get("memory_percent") or 0), float(info.get("cpu_percent") or 0), int(info["pid"]), info.get("name") or "Unknown"))
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess, TypeError, ValueError):
                continue
        items.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return items[:5]

    def sample(self):
        if not self.alive or not self.winfo_exists():
            return
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        cpu = float(psutil.cpu_percent(interval=0.25))
        ram = float(psutil.virtual_memory().percent)
        disk = float(self._disk_percent())
        processes = self._process_snapshot()
        snapshot = " | ".join(f"{name} (PID {pid}, RAM {memory:.1f}%, CPU {proc_cpu:.1f}%)" for memory, proc_cpu, pid, name in processes)
        try:
            with self._connect() as db:
                db.execute("INSERT INTO samples(timestamp,cpu,ram,disk,top_processes) VALUES(?,?,?,?,?)", (now, cpu, ram, disk, snapshot))
        except sqlite3.Error as error:
            self._set_diagnosis([f"Could not save history: {error}"])

        self.metric_labels["CPU"].configure(text=f"{cpu:.1f}%", text_color=RED if cpu >= self.CPU_LIMIT else WHITE)
        self.metric_labels["RAM"].configure(text=f"{ram:.1f}%", text_color=RED if ram >= self.RAM_LIMIT else WHITE)
        self.metric_labels["Disk"].configure(text=f"{disk:.1f}%", text_color=RED if disk >= self.DISK_LIMIT else WHITE)
        tips = self._diagnose(cpu, ram, disk, processes)
        self._set_diagnosis(tips)
        self._record_threshold_event("CPU", cpu >= self.CPU_LIMIT, f"CPU usage reached {cpu:.1f}%", snapshot, now)
        self._record_threshold_event("RAM", ram >= self.RAM_LIMIT, f"RAM usage reached {ram:.1f}%", snapshot, now)
        self._record_threshold_event("Disk", disk >= self.DISK_LIMIT, f"System drive usage reached {disk:.1f}%", snapshot, now)
        self.load_recent_events()
        if self.alive and self.winfo_exists():
            self.after_id = self.after(self.SAMPLE_SECONDS * 1000, self.sample)

    def _diagnose(self, cpu, ram, disk, processes):
        tips = []
        if cpu >= self.CPU_LIMIT:
            top_cpu = sorted(processes, key=lambda item: item[1], reverse=True)[:3]
            names = ", ".join(f"{name} ({value:.1f}% CPU)" for _, value, _, name in top_cpu if value > 0)
            tips.append(f"HIGH CPU: {cpu:.1f}% usage. Check whether an update, scan, browser tab, or heavy app is active.")
            if names:
                tips.append(f"Highest sampled process CPU: {names}. Process readings are approximate.")
        if ram >= self.RAM_LIMIT:
            top_ram = ", ".join(f"{name} ({memory:.1f}% RAM)" for memory, _, _, name in processes[:3])
            tips.append(f"HIGH MEMORY: {ram:.1f}% RAM in use. Save work, close unused apps/tabs, and investigate the largest consumers: {top_ram or 'not available'}.")
        if disk >= self.DISK_LIMIT:
            tips.append(f"LOW DISK SPACE: system drive is {disk:.1f}% used. Review large files and temporary files before removing anything.")
        if not tips:
            tips.append("HEALTHY: no configured resource threshold is currently exceeded.")
            tips.append("Tip: keep monitoring during your normal workload; a single sample cannot establish a persistent problem.")
        return tips

    def _set_diagnosis(self, lines):
        if not hasattr(self, "diagnosis") or not self.diagnosis.winfo_exists():
            return
        self.diagnosis.configure(state="normal")
        self.diagnosis.delete("1.0", "end")
        self.diagnosis.insert("end", "\n".join("• " + line for line in lines))
        self.diagnosis.configure(state="disabled")

    def _record_threshold_event(self, category, active, message, snapshot, timestamp):
        was_active = self.last_alert_state[category]
        self.last_alert_state[category] = active
        # Record once when crossing the threshold, not every five seconds.
        if active and not was_active:
            with self._connect() as db:
                db.execute("INSERT INTO events(timestamp,severity,category,message,process_snapshot) VALUES(?,?,?,?,?)", (timestamp, "WARNING", category, message, snapshot))

    def load_recent_events(self):
        if not hasattr(self, "events") or not self.events.winfo_exists():
            return
        try:
            with self._connect() as db:
                rows = db.execute("SELECT timestamp,severity,category,message,process_snapshot FROM events ORDER BY id DESC LIMIT 30").fetchall()
        except sqlite3.Error as error:
            rows = [(datetime.now().isoformat(timespec="seconds"), "ERROR", "Database", str(error), "")]
        self.events.delete("1.0", "end")
        if not rows:
            self.events.insert("end", "No warnings recorded yet. Thresholds: CPU ≥ 85%, RAM ≥ 85%, disk ≥ 90%.\n")
        for timestamp, severity, category, message, snapshot in rows:
            self.events.insert("end", f"[{timestamp}] {severity} | {category}: {message}\n  Processes: {snapshot or 'No snapshot'}\n\n")

    def export_csv(self):
        target = filedialog.asksaveasfilename(parent=self.winfo_toplevel(), title="Export resource history", defaultextension=".csv", filetypes=[("CSV file", "*.csv")], initialfile="systemscope_resource_history.csv")
        if not target:
            return
        try:
            with self._connect() as db, open(target, "w", newline="", encoding="utf-8-sig") as output:
                writer = csv.writer(output)
                writer.writerow(["timestamp", "cpu_percent", "ram_percent", "disk_percent", "top_processes"])
                writer.writerows(db.execute("SELECT timestamp,cpu,ram,disk,top_processes FROM samples ORDER BY id"))
            messagebox.showinfo("Export complete", "Resource history exported successfully.", parent=self.winfo_toplevel())
        except (OSError, sqlite3.Error) as error:
            messagebox.showerror("Export failed", str(error), parent=self.winfo_toplevel())

    def destroy(self):
        self.alive = False
        if self.after_id is not None:
            try:
                self.after_cancel(self.after_id)
            except (tk.TclError, RuntimeError):
                pass
            self.after_id = None
        super().destroy()
