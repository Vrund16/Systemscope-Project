"""SystemScope Suite — lightweight Windows PC monitoring and file utility dashboard."""
import os
import platform
import psutil
import customtkinter as ctk
import tkinter as tk
from collections import deque
from datetime import datetime

from modules.system_monitor import SystemMonitor
from modules.file_wizard import FileWizard
from modules.storage_analyzer import StorageAnalyzer
from modules.performance_doctor import PerformanceDoctor
from modules.reports import ReportsCenter
from modules.startup_analyzer import StartupAnalyzer
from modules.intelligence_center import IntelligenceCenter

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#080d19"
SIDEBAR = "#0d1424"
PANEL = "#111b2e"
PANEL_HOVER = "#1b2941"
BORDER = "#24334d"
BLUE = "#83a5ff"
CYAN = "#54d8d0"
GREEN = "#4adea5"
AMBER = "#f7c66a"
MUTED = "#91a0b9"
WHITE = "#f4f7ff"

class SystemScopeSuite(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SystemScope | PC Utility Suite")
        self.geometry("1380x860")
        self.minsize(980, 650)
        self.configure(fg_color=BG)
        self.active_module = None
        self.refresh_job = None
        self.current_page = "Overview"
        self.overview_active = False
        psutil.cpu_percent(interval=None)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=238, corner_radius=0, fg_color=SIDEBAR, border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)
        self._build_sidebar()
        self._build_topbar()
        self.show_overview()
        self._start_global_motion()
        self.protocol("WM_DELETE_WINDOW", self.close_app)

    def _build_sidebar(self):
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(26, 30))
        ctk.CTkLabel(brand, text="◈", text_color=CYAN, font=ctk.CTkFont(size=31, weight="bold")).pack(side="left", padx=(0, 9))
        titlebox = ctk.CTkFrame(brand, fg_color="transparent")
        titlebox.pack(side="left")
        ctk.CTkLabel(titlebox, text="SYSTEMSCOPE", text_color=WHITE, font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(titlebox, text="PC UTILITY SUITE  ·  SYSTEMSCOPE", text_color=MUTED, font=ctk.CTkFont(size=9, weight="bold")).pack(anchor="w", pady=(2,0))
        ctk.CTkLabel(self.sidebar, text="WORKSPACE", text_color="#667692", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=22, pady=(0, 9))
        nav = [
            ("⌂", "Overview", self.show_overview),
            ("◷", "System Monitor", self.show_system),
            ("▤", "FileWizard", self.show_files),
            ("▦", "Storage Intelligence", self.show_storage),
            ("✚", "Performance Doctor", self.show_doctor),
            ("◴", "Resource Reports", self.show_reports),
            ("↗", "Startup Analyzer", self.show_startup),
            ("✦", "PC Intelligence", self.show_intelligence),
        ]
        self.nav_buttons = {}
        for glyph, label, callback in nav:
            btn = ctk.CTkButton(self.sidebar, text=f"{glyph}    {label}", command=callback, anchor="w", height=43, corner_radius=10,
                fg_color="transparent", hover_color=PANEL_HOVER, text_color="#c9d5e9", font=ctk.CTkFont(size=13), border_spacing=12)
            btn.pack(fill="x", padx=12, pady=3)
            self.nav_buttons[label] = btn
        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER).pack(fill="x", padx=19, pady=22)
        status = ctk.CTkFrame(self.sidebar, fg_color=PANEL, corner_radius=12, border_width=1, border_color=BORDER)
        status.pack(side="bottom", fill="x", padx=14, pady=(0, 17))
        self.sidebar_status = ctk.CTkLabel(status, text="●  MONITORING READY", text_color=GREEN, font=ctk.CTkFont(size=10, weight="bold"))
        self.sidebar_status.pack(anchor="w", padx=12, pady=(12, 4))
        ctk.CTkLabel(status, text="Local-only · No cloud upload", text_color=MUTED, font=ctk.CTkFont(size=10)).pack(anchor="w", padx=12, pady=(0, 12))

    def _build_topbar(self):
        bar = ctk.CTkFrame(self.main, fg_color="#091326", corner_radius=0, height=66,
                           border_width=0)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)
        self.breadcrumb = ctk.CTkLabel(bar, text="WORKSPACE   /   OVERVIEW",
            text_color=MUTED, font=ctk.CTkFont(size=10, weight="bold"))
        self.breadcrumb.grid(row=0, column=0, sticky="w", padx=(22, 12), pady=18)
        search = ctk.CTkFrame(bar, fg_color="#101d33", corner_radius=16,
                              border_width=1, border_color="#203758")
        search.grid(row=0, column=1, sticky="ew", padx=8, pady=12)
        search.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(search, text="⌕", text_color=CYAN,
                     font=ctk.CTkFont(size=19, weight="bold")).grid(row=0, column=0, padx=(10, 4), pady=3)
        self.search_entry = ctk.CTkEntry(search, placeholder_text="Search tools…  (Ctrl+K)",
            width=210, height=29, fg_color="transparent", border_width=0,
            text_color=WHITE, placeholder_text_color="#7386a5", font=ctk.CTkFont(size=11))
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=3)
        self.search_entry.bind("<Return>", self._run_quick_search)
        self.bind_all("<Control-k>", lambda _e: (self.search_entry.focus_set(), "break"))
        self.live_dot = ctk.CTkLabel(bar, text="● LIVE", text_color=GREEN,
            font=ctk.CTkFont(size=10, weight="bold"))
        self.live_dot.grid(row=0, column=2, sticky="e", padx=(10, 12))
        self.clock = ctk.CTkLabel(bar, text="", text_color="#c6d2e6", font=ctk.CTkFont(size=10))
        self.clock.grid(row=0, column=3, sticky="e", padx=(0, 20))
        self._tick_clock()

    def _run_quick_search(self, _event=None):
        query = self.search_entry.get().strip().lower()
        routes = {
            "overview": self.show_overview, "dashboard": self.show_overview,
            "monitor": self.show_system, "system": self.show_system,
            "file": self.show_files, "filewizard": self.show_files,
            "storage": self.show_storage, "doctor": self.show_doctor,
            "performance": self.show_doctor, "report": self.show_reports,
            "startup": self.show_startup, "network": self.show_intelligence,
            "intelligence": self.show_intelligence, "radar": self.show_intelligence,
        }
        matches = [(key, fn) for key, fn in routes.items() if query and query in key]
        if matches:
            matches.sort(key=lambda item: len(item[0]), reverse=True)
            matches[0][1]()
        elif query:
            self.breadcrumb.configure(text=f"NO TOOL MATCH   /   {query.upper()[:28]}")
        self.search_entry.delete(0, "end")

    def _start_global_motion(self):
        """Subtle app-wide motion: live pulse, brand shimmer and active-page accent."""
        self._motion_phase = 0
        self._motion_colors = [GREEN, CYAN, BLUE, CYAN]
        self._animate_global_motion()

    def _animate_global_motion(self):
        if not self.winfo_exists():
            return
        self._motion_phase = (self._motion_phase + 1) % 4
        try:
            self.live_dot.configure(text="● LIVE" if self._motion_phase % 2 == 0 else "◉ LIVE",
                                    text_color=self._motion_colors[self._motion_phase])
            self.sidebar_status.configure(text_color=self._motion_colors[self._motion_phase])
        except Exception:
            return
        # 700ms pulse is intentionally modest to avoid burning CPU on animation.
        self._motion_job = self.after(700, self._animate_global_motion)

    def _tick_clock(self):
        if not self.winfo_exists(): return
        self.clock.configure(text=datetime.now().strftime("%a, %d %b  %H:%M:%S"))
        self.after(1000, self._tick_clock)

    def _set_active(self, page):
        self.current_page = page
        self.breadcrumb.configure(text=f"WORKSPACE   /   {page.upper()}")
        for label, button in self.nav_buttons.items():
            selected = label == page
            button.configure(fg_color="#1a2b49" if selected else "transparent",
                             text_color=CYAN if selected else "#c9d5e9",
                             border_width=1 if selected else 0,
                             border_color="#2e4b70" if selected else SIDEBAR)

    def _clear_content(self):
        self.overview_active = False
        if self.refresh_job is not None:
            try: self.after_cancel(self.refresh_job)
            except Exception: pass
            self.refresh_job = None
        if self.active_module is not None:
            try: self.active_module.destroy()
            except Exception: pass
            self.active_module = None
        # Topbar is always row 0; remove only the page at row 1.
        for child in list(self.main.winfo_children()):
            info = child.grid_info()
            if info and str(info.get("row")) == "1": child.destroy()

    def _page_frame(self, title, subtitle):
        frame = ctk.CTkFrame(self.main, fg_color=BG, corner_radius=0)
        frame.grid(row=1, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=title, text_color=WHITE, font=ctk.CTkFont(size=29, weight="bold")).pack(anchor="w", padx=26, pady=(23, 3))
        ctk.CTkLabel(frame, text=subtitle, text_color=MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=28, pady=(0, 18))
        return frame

    def _card(self, parent, title, accent, detail):
        card = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=15, border_width=1, border_color=BORDER)
        ctk.CTkLabel(card, text=title.upper(), text_color=MUTED, font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=16, pady=(15, 4))
        value = ctk.CTkLabel(card, text="—", text_color=accent, font=ctk.CTkFont(size=29, weight="bold"))
        value.pack(anchor="w", padx=16, pady=(0, 2))
        sub = ctk.CTkLabel(card, text=detail, text_color=MUTED, font=ctk.CTkFont(size=10))
        sub.pack(anchor="w", padx=16, pady=(0, 14))
        return card, value, sub

    def show_overview(self):
        self._clear_content()
        self._set_active("Overview")
        self.overview_active = True
        self.cpu_history = deque(maxlen=48)
        self.ram_history = deque(maxlen=48)
        self.disk_history = deque(maxlen=48)
        self._last_net = psutil.net_io_counters()
        self._last_net_time = __import__("time").monotonic()
        self._net_down = self._net_up = 0.0
        self.net_history = deque(maxlen=24)
        self._process_refresh_count = 0

        page = ctk.CTkScrollableFrame(self.main, fg_color=BG, corner_radius=0)
        page.grid(row=1, column=0, sticky="nsew")
        self._overview_page = page

        # Hero banner: crisp typography, glowing horizon art and clear live status.
        hero = ctk.CTkFrame(page, fg_color="#0b1a34", corner_radius=18,
                            border_width=1, border_color="#18385d")
        hero.pack(fill="x", padx=20, pady=(14, 11))
        hero.grid_columnconfigure(0, weight=1)
        left = ctk.CTkFrame(hero, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=21, pady=17)
        ctk.CTkLabel(left, text="SYSTEMSCOPE  /  PC COMMAND CENTRE", text_color=CYAN,
                     font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(left, text="Your PC. In full view.", text_color=WHITE,
                     font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left, text="Performance, storage and diagnostics — live, local and in your control.",
                     text_color="#a8bfdf", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(5, 10))
        self.health_status = ctk.CTkLabel(left, text="●  INITIALIZING LIVE TELEMETRY", text_color=GREEN,
                     font=ctk.CTkFont(size=10, weight="bold"))
        self.health_status.pack(anchor="w")
        art = tk.Canvas(hero, width=280, height=100, bg="#0b1a34", highlightthickness=0, bd=0)
        art.grid(row=0, column=1, sticky="e", padx=(0, 15), pady=6)
        art.create_oval(192, 2, 250, 60, fill="#142c66", outline="")
        art.create_oval(207, 9, 237, 39, fill="#2d59ad", outline="")
        art.create_polygon(0, 88, 42, 43, 72, 70, 114, 17, 157, 67, 202, 34, 280, 88,
                           fill="#142d59", outline="#24619a", width=1)
        art.create_polygon(42, 88, 114, 17, 157, 67, 183, 51, 224, 88,
                           fill="#102447", outline="#1c5790", width=1)
        art.create_line(66, 91, 244, 91, fill=CYAN, width=2)
        art.create_oval(153, 87, 161, 95, fill=CYAN, outline="")
        self._hero_art = art

        # Four live cards, matching the reference's CPU / RAM / disk / network hierarchy.
        cards = ctk.CTkFrame(page, fg_color="transparent")
        cards.pack(fill="x", padx=16)
        for i in range(4): cards.grid_columnconfigure(i, weight=1, uniform="metric")
        specs = [
            ("CPU USAGE", BLUE, "Processor utilization", self.show_system, "◈"),
            ("MEMORY", CYAN, "Physical memory in use", self.show_system, "▣"),
            ("SYSTEM DRIVE", AMBER, "System volume usage", self.show_storage, "▤"),
            ("NETWORK RATE", "#a78bfa", "Current receive / send", self.show_intelligence, "⌁"),
        ]
        self.metric_values = {}; self.metric_subs = {}; self.metric_bars = {}; self.metric_cards = {}
        for i, (name, color, detail, command, glyph) in enumerate(specs):
            card = ctk.CTkFrame(cards, fg_color="#0d1a2e", corner_radius=15,
                                border_width=1, border_color="#1b3556")
            card.grid(row=0, column=i, sticky="ew", padx=4, pady=4)
            self.metric_cards[name] = card
            head = ctk.CTkFrame(card, fg_color="transparent")
            head.pack(fill="x", padx=12, pady=(11, 3))
            ctk.CTkLabel(head, text=glyph, text_color=color,
                         font=ctk.CTkFont(size=17, weight="bold")).pack(side="left", padx=(0, 7))
            ctk.CTkLabel(head, text=name, text_color="#b7c9e5",
                         font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")
            value = ctk.CTkLabel(card, text="—", text_color=color,
                         font=ctk.CTkFont(size=24, weight="bold"))
            value.pack(anchor="w", padx=13)
            sub = ctk.CTkLabel(card, text=detail, text_color=MUTED,
                         font=ctk.CTkFont(size=9))
            sub.pack(anchor="w", padx=13, pady=(0, 8))
            bar = ctk.CTkProgressBar(card, height=4, progress_color=color, fg_color="#1d2d47")
            bar.pack(fill="x", padx=13, pady=(0, 12)); bar.set(0)
            if name == "NETWORK RATE":
                # Network traffic is a rate, not a percentage: use a sparkline instead of a misleading percent bar.
                bar.pack_forget()
                spark = tk.Canvas(card, height=17, bg="#0d1a2e", highlightthickness=0, bd=0)
                spark.pack(fill="x", padx=12, pady=(0, 9))
                self.net_sparkline = spark
            self.metric_values[name] = value; self.metric_subs[name] = sub; self.metric_bars[name] = bar
            for widget in (card, head, value, sub):
                widget.bind("<Button-1>", lambda _e, fn=command: fn())
                widget.bind("<Enter>", lambda _e, w=card: w.configure(border_color="#3474a7"))
                widget.bind("<Leave>", lambda _e, w=card: w.configure(border_color="#1b3556"))

        # Main analytics: wide chart + health score panel.
        analytics = ctk.CTkFrame(page, fg_color="transparent")
        analytics.pack(fill="x", padx=16, pady=(7, 3))
        analytics.grid_columnconfigure(0, weight=7, uniform="analytics")
        analytics.grid_columnconfigure(1, weight=4, uniform="analytics")
        trend = ctk.CTkFrame(analytics, fg_color="#0d1a2e", corner_radius=16,
                             border_width=1, border_color="#1b3556")
        trend.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        trend_head = ctk.CTkFrame(trend, fg_color="transparent")
        trend_head.pack(fill="x", padx=15, pady=(12, 0))
        ctk.CTkLabel(trend_head, text="〰  PERFORMANCE PULSE", text_color=WHITE,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        ctk.CTkLabel(trend_head, text="● LIVE", text_color=CYAN,
                     font=ctk.CTkFont(size=9, weight="bold")).pack(side="right")
        ctk.CTkLabel(trend, text="Recent samples · CPU and memory utilization",
                     text_color=MUTED, font=ctk.CTkFont(size=10)).pack(anchor="w", padx=16, pady=(3, 2))
        self.pulse_canvas = tk.Canvas(trend, height=155, bg="#0d1a2e", highlightthickness=0, bd=0)
        self.pulse_canvas.pack(fill="x", padx=10, pady=(0, 10))
        self.pulse_canvas.bind("<Configure>", lambda _e: self._draw_pulse())
        self._pulse_phase = 0
        self._pulse_marker_job = None
        self._animate_pulse_marker()

        health = ctk.CTkFrame(analytics, fg_color="#0d1a2e", corner_radius=16,
                              border_width=1, border_color="#1b3556")
        health.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        ctk.CTkLabel(health, text="✦  PC HEALTH SCORE", text_color=WHITE,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(12, 2))
        self.health_gauge = tk.Canvas(health, width=190, height=125, bg="#0d1a2e", highlightthickness=0, bd=0)
        self.health_gauge.pack(pady=(0, 0))
        self.health_score = ctk.CTkLabel(health, text="— / 100", text_color=GREEN,
                     font=ctk.CTkFont(size=20, weight="bold"))
        self.health_score.pack()
        ctk.CTkLabel(health, text="Resource-pressure estimate, not hardware health", text_color=MUTED,
                     font=ctk.CTkFont(size=9), wraplength=250).pack(pady=(1, 11), padx=10)

        # Quick launch row with real routes into existing modules.
        quick = ctk.CTkFrame(page, fg_color="transparent")
        quick.pack(fill="x", padx=16, pady=(6, 3))
        actions = [
            ("⌁", "Network App Detective", "Inspect active connections", self.show_intelligence, CYAN),
            ("◉", "Storage Change Radar", "Compare folder snapshots", self.show_storage, GREEN),
            ("✚", "Performance Doctor", "Warnings and resource history", self.show_doctor, "#b69cff"),
            ("▤", "FileWizard", "Browse and organize files", self.show_files, BLUE),
        ]
        for i, (glyph, label, desc, command, color) in enumerate(actions):
            quick.grid_columnconfigure(i, weight=1, uniform="quick")
            item = ctk.CTkFrame(quick, fg_color="#101f36", corner_radius=13,
                                border_width=1, border_color="#1d3657")
            item.grid(row=0, column=i, sticky="ew", padx=4, pady=4)
            ctk.CTkLabel(item, text=glyph, text_color=color,
                         font=ctk.CTkFont(size=21, weight="bold")).pack(anchor="w", padx=12, pady=(8, 0))
            ctk.CTkButton(item, text=label, command=command, anchor="w", height=27,
                          fg_color="transparent", hover_color="#1c3454", text_color=WHITE,
                          font=ctk.CTkFont(size=10, weight="bold")).pack(fill="x", padx=4)
            ctk.CTkLabel(item, text=desc, text_color=MUTED,
                         font=ctk.CTkFont(size=9)).pack(anchor="w", padx=12, pady=(0, 8))

        # Lower dashboard: real top processes, storage distribution and recent activity.
        lower = ctk.CTkFrame(page, fg_color="transparent")
        lower.pack(fill="x", padx=16, pady=(5, 8))
        for i, weight in enumerate((5, 3, 3)): lower.grid_columnconfigure(i, weight=weight, uniform="lower")

        process_panel = ctk.CTkFrame(lower, fg_color="#0d1a2e", corner_radius=15,
                                     border_width=1, border_color="#1b3556")
        process_panel.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        ph = ctk.CTkFrame(process_panel, fg_color="transparent")
        ph.pack(fill="x", padx=13, pady=(12, 7))
        ctk.CTkLabel(ph, text="▣  RUNNING PROCESSES", text_color=WHITE,
                     font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkButton(ph, text="Open monitor  ↗", command=self.show_system, width=100, height=24,
                      fg_color="#172b47", hover_color="#25456d", text_color=CYAN,
                      font=ctk.CTkFont(size=9)).pack(side="right")
        header = ctk.CTkFrame(process_panel, fg_color="#13223a", corner_radius=7)
        header.pack(fill="x", padx=10, pady=(0, 3))
        for col, label, width in ((0,"PROCESS",1),(1,"PID",1),(2,"MEMORY",1)):
            header.grid_columnconfigure(col, weight=width)
            ctk.CTkLabel(header, text=label, text_color=MUTED, font=ctk.CTkFont(size=8, weight="bold")).grid(row=0,column=col,sticky="w",padx=6,pady=5)
        self.process_rows = ctk.CTkFrame(process_panel, fg_color="transparent")
        self.process_rows.pack(fill="x", padx=10, pady=(0, 9))

        storage_panel = ctk.CTkFrame(lower, fg_color="#0d1a2e", corner_radius=15,
                                     border_width=1, border_color="#1b3556")
        storage_panel.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        ctk.CTkLabel(storage_panel, text="◉  STORAGE", text_color=WHITE,
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=13, pady=(12, 2))
        self.storage_canvas = tk.Canvas(storage_panel, height=118, bg="#0d1a2e", highlightthickness=0, bd=0)
        self.storage_canvas.pack(fill="x", padx=6, pady=(0, 0))
        self.storage_detail = ctk.CTkLabel(storage_panel, text="Waiting for disk data…", text_color=MUTED,
                     font=ctk.CTkFont(size=9), justify="left")
        self.storage_detail.pack(anchor="w", padx=13, pady=(0, 6))
        ctk.CTkButton(storage_panel, text="Open Storage Intelligence  →", command=self.show_storage,
                      height=27, fg_color="#122d50", hover_color="#1b4773", text_color=CYAN,
                      font=ctk.CTkFont(size=9, weight="bold")).pack(fill="x", padx=10, pady=(0, 10))

        activity_panel = ctk.CTkFrame(lower, fg_color="#0d1a2e", corner_radius=15,
                                       border_width=1, border_color="#1b3556")
        activity_panel.grid(row=0, column=2, sticky="nsew", padx=4, pady=4)
        ctk.CTkLabel(activity_panel, text="◷  SESSION ACTIVITY", text_color=WHITE,
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=13, pady=(12, 7))
        self.activity_text = ctk.CTkLabel(activity_panel,
            text="● Monitoring started\n● Local-only telemetry\n● No changes made", text_color=MUTED,
            justify="left", anchor="w", font=ctk.CTkFont(size=9))
        self.activity_text.pack(fill="x", padx=13, pady=(0, 12))

        # Device snapshot panel: refresh_overview updates this widget every cycle.
        snapshot_panel = ctk.CTkFrame(page, fg_color="#0d1a2e", corner_radius=14,
                                      border_width=1, border_color="#1b3556")
        snapshot_panel.pack(fill="x", padx=20, pady=(5, 8))
        ctk.CTkLabel(snapshot_panel, text="DEVICE SNAPSHOT", text_color=CYAN,
                     font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=14, pady=(10, 4))
        self.snapshot = ctk.CTkLabel(
            snapshot_panel,
            text="Collecting device details…",
            text_color=MUTED,
            justify="left",
            anchor="w",
            wraplength=1100,
            font=ctk.CTkFont(size=10),
        )
        self.snapshot.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(page, text="LOCAL-FIRST  ·  REAL SYSTEM TELEMETRY  ·  NO AUTOMATIC CLEANUP",
                     text_color="#7183a0", font=ctk.CTkFont(size=9, weight="bold")).pack(anchor="w", padx=25, pady=(4, 15))
        self.refresh_overview()

    def _draw_pulse(self):
        canvas = getattr(self, "pulse_canvas", None)
        if canvas is None or not canvas.winfo_exists(): return
        canvas.delete("all")
        width = max(canvas.winfo_width(), 220); height = max(canvas.winfo_height(), 100)
        left, right, top, bottom = 38, width - 12, 12, height - 20
        for pct in (0, 25, 50, 75, 100):
            y = bottom - (bottom - top) * pct / 100
            canvas.create_line(left, y, right, y, fill="#25334a", dash=(2, 4))
        canvas.create_text(2, top, text="100%", anchor="nw", fill="#7183a0", font=("Segoe UI", 8))
        canvas.create_text(2, bottom, text="0%", anchor="sw", fill="#7183a0", font=("Segoe UI", 8))
        def draw(values, color):
            if len(values) < 2: return
            points = []
            for i, value in enumerate(values):
                x = left + (right-left) * i / max(1, len(values)-1)
                y = bottom - (bottom-top) * max(0, min(100, value)) / 100
                points.extend((x, y))
            canvas.create_line(*points, fill=color, width=2, smooth=True)
        draw(list(self.cpu_history), BLUE)
        draw(list(self.ram_history), CYAN)
        canvas.create_text(right - 92, top, text="● CPU", anchor="nw", fill=BLUE, font=("Segoe UI", 9, "bold"))
        canvas.create_text(right - 45, top, text="● RAM", anchor="nw", fill=CYAN, font=("Segoe UI", 9, "bold"))

    def _draw_network_sparkline(self):
        canvas = getattr(self, "net_sparkline", None)
        if canvas is None or not canvas.winfo_exists():
            return
        canvas.delete("all")
        values = list(getattr(self, "net_history", []))
        width = max(canvas.winfo_width(), 150)
        height = max(canvas.winfo_height(), 17)
        canvas.create_line(0, height - 2, width, height - 2, fill="#1d3554", width=1)
        if len(values) < 2:
            canvas.create_text(2, 2, text="Collecting network samples…", anchor="nw", fill=MUTED,
                               font=("Segoe UI", 7))
            return
        peak = max(max(values), 1.0)
        points = []
        for i, value in enumerate(values):
            x = (width - 4) * i / max(1, len(values) - 1) + 2
            y = height - 2 - (height - 5) * value / peak
            points.extend((x, y))
        canvas.create_line(*points, fill="#a78bfa", width=2, smooth=True)

    def _draw_storage(self, used_percent, used_gb, total_gb):
        canvas = getattr(self, "storage_canvas", None)
        if canvas is None or not canvas.winfo_exists(): return
        canvas.delete("all")
        width = max(canvas.winfo_width(), 170)
        cx, cy, radius = width / 2, 57, 40
        canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, outline="#253955", width=11)
        canvas.create_arc(cx-radius, cy-radius, cx+radius, cy+radius, start=90,
                          extent=-360*max(0,min(100,used_percent))/100, style="arc",
                          outline=CYAN, width=11)
        canvas.create_text(cx, cy-4, text=f"{used_percent:.0f}%", fill=WHITE, font=("Segoe UI", 17, "bold"))
        canvas.create_text(cx, cy+16, text="USED", fill=MUTED, font=("Segoe UI", 8, "bold"))
        self.storage_detail.configure(text=f"{used_gb:.0f} GB used\n{max(0,total_gb-used_gb):.0f} GB free")

    def _refresh_process_list(self):
        if not hasattr(self, "process_rows") or not self.process_rows.winfo_exists(): return
        for child in self.process_rows.winfo_children(): child.destroy()
        rows = []
        try:
            for proc in psutil.process_iter(["pid", "name", "memory_info"]):
                try:
                    info = proc.info
                    mem = info.get("memory_info")
                    rows.append((int(mem.rss) if mem else 0, info.get("name") or "Unknown", info.get("pid", "—")))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except psutil.Error:
            rows = []
        for _, name, pid in sorted(rows, reverse=True)[:6]:
            row = ctk.CTkFrame(self.process_rows, fg_color="transparent")
            row.pack(fill="x", pady=1)
            row.grid_columnconfigure(0, weight=3)
            row.grid_columnconfigure(1, weight=1)
            row.grid_columnconfigure(2, weight=1)
            ctk.CTkLabel(row, text=name[:22], text_color="#d5e2f7", anchor="w",
                         font=ctk.CTkFont(size=9)).grid(row=0,column=0,sticky="ew",padx=6,pady=4)
            ctk.CTkLabel(row, text=str(pid), text_color=MUTED, anchor="w",
                         font=ctk.CTkFont(size=9)).grid(row=0,column=1,sticky="ew",padx=6,pady=4)
            ctk.CTkLabel(row, text=f"{_ / (1024**2):.0f} MB", text_color=CYAN, anchor="w",
                         font=ctk.CTkFont(size=9)).grid(row=0,column=2,sticky="ew",padx=6,pady=4)

    def _animate_pulse_marker(self):
        if not getattr(self, "overview_active", False) or not self.winfo_exists(): return
        canvas = getattr(self, "pulse_canvas", None)
        if canvas is not None and canvas.winfo_exists():
            canvas.delete("motion-marker")
            self._pulse_phase = (getattr(self, "_pulse_phase", 0) + 1) % 12
            width = max(canvas.winfo_width(), 220)
            x = 42 + (width - 58) * self._pulse_phase / 11
            canvas.create_oval(x-3, 9, x+3, 15, fill=CYAN, outline="", tags="motion-marker")
        self._pulse_marker_job = self.after(150, self._animate_pulse_marker)

    def refresh_overview(self):
        if not self.overview_active or not self.winfo_exists(): return
        try:
            # Non-blocking sample: psutil.cpu_percent is primed once during app startup.
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            drive = os.environ.get("SystemDrive", "C:") + "\\"
            try:
                disk = psutil.disk_usage(drive)
            except (OSError, PermissionError):
                disk = psutil.disk_usage(os.path.abspath(os.sep))
            now = __import__("time").monotonic()
            net = psutil.net_io_counters()
            previous = getattr(self, "_last_net", net)
            elapsed = max(0.001, now - getattr(self, "_last_net_time", now))
            down = max(0.0, (net.bytes_recv - previous.bytes_recv) / elapsed)
            up = max(0.0, (net.bytes_sent - previous.bytes_sent) / elapsed)
            self._last_net, self._last_net_time = net, now
            self._net_down, self._net_up = down, up
            process_count = len(psutil.pids())
            values = {"CPU USAGE": cpu, "MEMORY": mem.percent, "SYSTEM DRIVE": disk.percent}
            for key, val in values.items():
                self.metric_values[key].configure(text=f"{val:.1f}%")
                self.metric_bars[key].set(max(0, min(100, val)) / 100)
            self.metric_subs["MEMORY"].configure(text=f"{mem.used/(1024**3):.1f} / {mem.total/(1024**3):.1f} GB")
            self.metric_subs["SYSTEM DRIVE"].configure(text=f"{disk.free/(1024**3):.1f} GB free")
            self.metric_values["NETWORK RATE"].configure(text=f"↓ {down/1024:.1f} KB/s")
            self.metric_subs["NETWORK RATE"].configure(text=f"↑ {up/1024:.1f} KB/s sent")
            self.net_history.append(down + up)
            self._draw_network_sparkline()
            self.cpu_history.append(cpu); self.ram_history.append(mem.percent); self.disk_history.append(disk.percent)
            self._draw_pulse()
            # Heuristic is explicitly a current pressure estimate, not hardware health.
            pressure = max(0, cpu - 65) * 0.35 + max(0, mem.percent - 70) * 0.45 + max(0, disk.percent - 85) * 0.20
            score = max(0, min(100, round(100 - pressure)))
            score_color = GREEN if score >= 80 else AMBER if score >= 60 else "#fb7185"
            self.health_score.configure(text=f"{score}/100", text_color=score_color)
            if score >= 80: status, color = "●  SYSTEM PRESSURE LOOKS NORMAL", GREEN
            elif score >= 60: status, color = "●  SOME RESOURCE PRESSURE DETECTED", AMBER
            else: status, color = "●  HIGH RESOURCE PRESSURE — INVESTIGATE", "#fb7185"
            self.health_status.configure(text=status, text_color=color)
            if hasattr(self, "health_gauge") and self.health_gauge.winfo_exists():
                g = self.health_gauge; g.delete("all")
                g.create_arc(24, 7, 166, 149, start=135, extent=270, style="arc", outline="#263955", width=10)
                g.create_arc(24, 7, 166, 149, start=135, extent=270*score/100, style="arc", outline=score_color, width=10)
                g.create_text(95, 67, text=str(score), fill=WHITE, font=("Segoe UI", 24, "bold"))
                g.create_text(95, 92, text="LOAD SCORE", fill=MUTED, font=("Segoe UI", 8, "bold"))
            used_gb, total_gb = disk.used/(1024**3), disk.total/(1024**3)
            self._draw_storage(disk.percent, used_gb, total_gb)
            uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
            self.snapshot.configure(text=f"Device: {platform.node()}   •   OS: {platform.system()} {platform.release()}   •   Logical CPUs: {psutil.cpu_count(logical=True)}\nUptime: {str(uptime).split('.')[0]}   •   RAM available: {mem.available/(1024**3):.1f} GB\nSystem drive: {drive}   •   {disk.free/(1024**3):.1f} GB free of {disk.total/(1024**3):.1f} GB\nNetwork: ↓ {down/1024:.1f} KB/s   ↑ {up/1024:.1f} KB/s   •   Updated: {datetime.now().strftime('%H:%M:%S')}\nScore estimates current CPU/RAM/disk pressure; it is not hardware health certification.")
            self._process_refresh_count += 1
            if self._process_refresh_count % 3 == 1:
                self._refresh_process_list()
            self.activity_text.configure(text=f"● Telemetry refreshed · {datetime.now().strftime('%H:%M:%S')}\n● CPU {cpu:.1f}% / RAM {mem.percent:.1f}%\n● Network ↓ {down/1024:.1f} KB/s · ↑ {up/1024:.1f} KB/s\n● Read-only monitoring active")
        except (OSError, ValueError, KeyError, psutil.Error) as exc:
            if hasattr(self, "snapshot") and self.snapshot.winfo_exists():
                self.snapshot.configure(text=f"Some system details are unavailable: {exc}")
        if self.overview_active: self.refresh_job = self.after(3000, self.refresh_overview)

    def _open_module(self, page, title, subtitle, cls):
        self._clear_content(); self._set_active(page)
        self.active_module=cls(self.main); self.active_module.grid(row=1,column=0,sticky="nsew")

    def show_system(self): self._open_module("System Monitor","","",SystemMonitor)
    def show_files(self): self._open_module("FileWizard","","",FileWizard)
    def show_storage(self): self._open_module("Storage Intelligence","","",StorageAnalyzer)
    def show_doctor(self): self._open_module("Performance Doctor","","",PerformanceDoctor)
    def show_reports(self): self._open_module("Resource Reports","","",ReportsCenter)
    def show_startup(self): self._open_module("Startup Analyzer","","",StartupAnalyzer)
    def show_intelligence(self): self._open_module("PC Intelligence","","",IntelligenceCenter)

    def close_app(self):
        self.overview_active=False
        for job_name in ("_motion_job", "_pulse_marker_job"):
            job = getattr(self, job_name, None)
            if job is not None:
                try: self.after_cancel(job)
                except Exception: pass
        if self.refresh_job is not None:
            try: self.after_cancel(self.refresh_job)
            except Exception: pass
        self.destroy()

if __name__ == "__main__":
    app=SystemScopeSuite()
    app.mainloop()
