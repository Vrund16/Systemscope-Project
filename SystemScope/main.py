
import tkinter as tk
import customtkinter as ctk
import psutil
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------- SETTINGS ----------------
APP_TITLE = "SystemScope | PC Health Monitor"
REFRESH_MS = 1000
PROCESS_REFRESH_MS = 3000
CPU_ALERT = 85
RAM_ALERT = 85
HISTORY_SIZE = 60

BG = "#0B1020"
SIDEBAR = "#0E1629"
PANEL = "#141F33"
CARD = "#18263D"
BORDER = "#293954"
TEXT = "#EDF4FF"
MUTED = "#91A3BD"
CYAN = "#45D6E8"
PURPLE = "#A78BFA"
GREEN = "#42D392"
RED = "#FF647C"
ORANGE = "#F6B85E"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SystemScope(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1280x850")
        self.minsize(1000, 700)
        self.configure(fg_color=BG)

        self.closing = False
        self.metric_job = None
        self.process_job = None

        self.cpu_history = []
        self.ram_history = []
        self.process_rows = []
        self.current_page = "Overview"

        self.metric_widgets = {}
        self.graphs = {}
        self.alert_label = None
        self.process_table_frame = None
        self.top_process_frame = None
        self.search_entry = None

        self.protocol("WM_DELETE_WINDOW", self.close_app)

        # Prime CPU readings before the first refresh.
        psutil.cpu_percent(interval=None)

        self.build_layout()
        self.show_page("Overview")
        self.update_metrics()
        self.refresh_processes()

    # ---------------- MAIN LAYOUT ----------------

    def build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(
            self, width=210, corner_radius=0, fg_color=SIDEBAR
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="◈ SYSTEM\n   SCOPE",
            font=("Segoe UI", 24, "bold"),
            text_color=CYAN,
            justify="left"
        ).pack(anchor="w", padx=22, pady=(28, 5))

        ctk.CTkLabel(
            self.sidebar,
            text="PC HEALTH MONITOR",
            font=("Segoe UI", 10, "bold"),
            text_color=MUTED
        ).pack(anchor="w", padx=24, pady=(0, 28))

        self.nav_buttons = {}

        for page, symbol in [
            ("Overview", "▦"),
            ("Processes", "▤"),
            ("Performance", "⌁"),
            ("About", "ⓘ")
        ]:
            button = ctk.CTkButton(
                self.sidebar,
                text=f"{symbol}    {page}",
                anchor="w",
                height=44,
                corner_radius=10,
                fg_color="transparent",
                hover_color=PANEL,
                text_color=TEXT,
                font=("Segoe UI", 13),
                command=lambda p=page: self.show_page(p)
            )
            button.pack(fill="x", padx=13, pady=4)
            self.nav_buttons[page] = button

        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=BORDER
        ).pack(fill="x", padx=18, pady=(22, 14))

        ctk.CTkLabel(
            self.sidebar,
            text="●  LIVE MONITORING",
            text_color=GREEN,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=20, pady=5)

        ctk.CTkLabel(
            self.sidebar,
            text="Automatic updates\nEvery second",
            text_color=MUTED,
            justify="left",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=22)

        ctk.CTkLabel(
            self.sidebar,
            text="SYSTEMSCOPE • MVP",
            text_color="#61738F",
            font=("Segoe UI", 9, "bold")
        ).pack(side="bottom", anchor="w", padx=20, pady=18)

        self.main = ctk.CTkFrame(
            self, fg_color=BG, corner_radius=0
        )
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(
            self.main, fg_color=BG, corner_radius=0
        )
        header.grid(
            row=0, column=0, sticky="ew",
            padx=28, pady=(24, 10)
        )
        header.grid_columnconfigure(0, weight=1)

        self.page_title = ctk.CTkLabel(
            header,
            text="Overview",
            text_color=TEXT,
            font=("Segoe UI", 26, "bold")
        )
        self.page_title.grid(row=0, column=0, sticky="w")

        self.clock_label = ctk.CTkLabel(
            header,
            text="",
            text_color=MUTED,
            font=("Segoe UI", 11)
        )
        self.clock_label.grid(row=0, column=1, sticky="e")

        self.content = ctk.CTkScrollableFrame(
            self.main,
            fg_color=BG,
            corner_radius=0,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color="#405675"
        )
        self.content.grid(
            row=1, column=0, sticky="nsew",
            padx=20, pady=(0, 12)
        )
        self.content.grid_columnconfigure(0, weight=1)

    # ---------------- NAVIGATION ----------------

    def show_page(self, page):
        self.current_page = page
        self.page_title.configure(text=page)

        for name, button in self.nav_buttons.items():
            button.configure(
                fg_color=PANEL if name == page else "transparent",
                text_color=CYAN if name == page else TEXT
            )

        for child in self.content.winfo_children():
            child.destroy()

        # Old page widgets are destroyed; reset their references.
        self.metric_widgets = {}
        self.graphs = {}
        self.alert_label = None
        self.process_table_frame = None
        self.top_process_frame = None
        self.search_entry = None

        if page == "Overview":
            self.build_overview()
        elif page == "Processes":
            self.build_process_page()
        elif page == "Performance":
            self.build_performance_page()
        else:
            self.build_about_page()

    def section_label(self, parent, text):
        ctk.CTkLabel(
            parent,
            text=text.upper(),
            text_color=MUTED,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=3, pady=(10, 10))

    # ---------------- OVERVIEW ----------------

    def build_overview(self):
        self.section_label(self.content, "System overview")

        cards = ctk.CTkFrame(
            self.content, fg_color="transparent"
        )
        cards.pack(fill="x", pady=(0, 14))
        cards.grid_columnconfigure((0, 1, 2), weight=1, uniform="cards")

        card_data = [
            ("cpu", "CPU USAGE", CYAN),
            ("ram", "MEMORY USAGE", PURPLE),
            ("disk", "DISK USAGE · C:", GREEN)
        ]

        for col, (key, title, accent) in enumerate(card_data):
            card = ctk.CTkFrame(
                cards,
                fg_color=CARD,
                corner_radius=14,
                border_width=1,
                border_color=BORDER
            )
            card.grid(
                row=0, column=col, sticky="nsew",
                padx=(0 if col == 0 else 6,
                      0 if col == 2 else 6)
            )

            ctk.CTkFrame(
                card, height=4, fg_color=accent,
                corner_radius=4
            ).pack(fill="x", padx=1, pady=(1, 0))

            ctk.CTkLabel(
                card,
                text=title,
                text_color=MUTED,
                font=("Segoe UI", 10, "bold")
            ).pack(anchor="w", padx=16, pady=(16, 4))

            value = ctk.CTkLabel(
                card, text="--%",
                text_color=accent,
                font=("Segoe UI", 30, "bold")
            )
            value.pack(anchor="w", padx=16)

            detail = ctk.CTkLabel(
                card, text="Waiting for readings...",
                text_color=MUTED,
                font=("Segoe UI", 10)
            )
            detail.pack(anchor="w", padx=16, pady=(4, 10))

            progress = ctk.CTkProgressBar(
                card, height=5,
                progress_color=accent,
                fg_color=BORDER
            )
            progress.pack(fill="x", padx=16, pady=(0, 16))
            progress.set(0)

            self.metric_widgets[key] = (value, detail, progress)

        alert_box = ctk.CTkFrame(
            self.content,
            fg_color=PANEL,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )
        alert_box.pack(fill="x", pady=(0, 16))

        self.alert_label = ctk.CTkLabel(
            alert_box,
            text="●  Collecting system status...",
            text_color=GREEN,
            font=("Segoe UI", 12, "bold")
        )
        self.alert_label.pack(anchor="w", padx=16, pady=14)

        self.section_label(self.content, "Performance history")

        graph_row = ctk.CTkFrame(
            self.content, fg_color="transparent"
        )
        graph_row.pack(fill="x", pady=(0, 16))
        graph_row.grid_columnconfigure((0, 1), weight=1, uniform="graphs")

        self.graphs["cpu"] = self.make_graph(
            graph_row, "CPU UTILIZATION", CYAN, 0
        )
        self.graphs["ram"] = self.make_graph(
            graph_row, "MEMORY UTILIZATION", PURPLE, 1
        )

        process_header = ctk.CTkFrame(
            self.content, fg_color="transparent"
        )
        process_header.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            process_header, text="TOP PROCESSES",
            text_color=MUTED,
            font=("Segoe UI", 11, "bold")
        ).pack(side="left")

        ctk.CTkButton(
            process_header, text="View all →",
            width=100, height=30, corner_radius=8,
            fg_color=PANEL, hover_color=BORDER,
            text_color=CYAN,
            command=lambda: self.show_page("Processes")
        ).pack(side="right")

        self.top_process_frame = ctk.CTkFrame(
            self.content, fg_color=CARD,
            corner_radius=12, border_width=1,
            border_color=BORDER
        )
        self.top_process_frame.pack(fill="x", pady=(0, 8))
        self.draw_process_table(self.top_process_frame, limit=5)

    # ---------------- GRAPHS ----------------

    def make_graph(self, parent, title, color, column):
        frame = ctk.CTkFrame(
            parent, fg_color=CARD, corner_radius=14,
            border_width=1, border_color=BORDER
        )
        frame.grid(
            row=0, column=column, sticky="nsew",
            padx=(0 if column == 0 else 6,
                  0 if column == 1 else 6)
        )

        ctk.CTkLabel(
            frame, text=title, text_color=TEXT,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=14, pady=(12, 0))

        value = ctk.CTkLabel(
            frame, text="0.0%", text_color=color,
            font=("Segoe UI", 21, "bold")
        )
        value.pack(anchor="w", padx=14, pady=(2, 0))

        fig = Figure(figsize=(4.5, 1.8), dpi=100, facecolor=CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(CARD)
        ax.set_ylim(0, 100)
        ax.set_xlim(0, HISTORY_SIZE - 1)
        ax.set_yticks([0, 50, 100])
        ax.set_xticks([])
        ax.tick_params(colors=MUTED, labelsize=8, length=0)

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.grid(axis="y", color=BORDER, linestyle="--", linewidth=0.7)
        line, = ax.plot([], [], color=color, linewidth=2)

        fig.subplots_adjust(left=0.09, right=0.98, top=0.96, bottom=0.12)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().pack(fill="x", padx=8, pady=(0, 8))

        return {
            "frame": frame,
            "value": value,
            "ax": ax,
            "line": line,
            "canvas": canvas
        }

    def update_graph(self, graph, history, current):
        graph["value"].configure(text=f"{current:.1f}%")

        values = list(history)
        graph["line"].set_data(range(len(values)), values)
        graph["canvas"].draw_idle()

    def build_performance_page(self):
        self.section_label(self.content, "Live resource utilization")

        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x")
        row.grid_columnconfigure((0, 1), weight=1, uniform="largegraphs")

        self.graphs["cpu_large"] = self.make_graph(
            row, "CPU UTILIZATION", CYAN, 0
        )
        self.graphs["ram_large"] = self.make_graph(
            row, "MEMORY UTILIZATION", PURPLE, 1
        )

        ctk.CTkLabel(
            self.content,
            text="Showing the last 60 readings (approximately one minute).",
            text_color=MUTED, font=("Segoe UI", 11)
        ).pack(anchor="w", pady=12)

    # ---------------- PROCESS MANAGER ----------------

    def build_process_page(self):
        self.section_label(self.content, "Running processes")

        toolbar = ctk.CTkFrame(
            self.content, fg_color="transparent"
        )
        toolbar.pack(fill="x", pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="Search process name or PID...",
            height=38, corner_radius=10,
            border_color=BORDER, fg_color=CARD
        )
        self.search_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        self.search_entry.bind(
            "<KeyRelease>", self.on_process_search
        )

        ctk.CTkButton(
            toolbar, text="Refresh now",
            width=115, height=38, corner_radius=10,
            fg_color="#1A5263", hover_color="#216B7E",
            command=self.refresh_processes
        ).pack(side="right")

        ctk.CTkLabel(
            self.content,
            text="Sorted by memory usage. Some protected Windows processes may be unavailable.",
            text_color=MUTED, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(0, 10))

        self.process_table_frame = ctk.CTkFrame(
            self.content, fg_color=CARD,
            corner_radius=12, border_width=1,
            border_color=BORDER
        )
        self.process_table_frame.pack(fill="both", expand=True)
        self.draw_process_table(self.process_table_frame)

    def on_process_search(self, _event=None):
        if self.process_table_frame is not None:
            self.draw_process_table(self.process_table_frame)

    def draw_process_table(self, parent, limit=None):
        for child in parent.winfo_children():
            child.destroy()

        headings = [
            ("PID", 0.13),
            ("PROCESS", 0.45),
            ("CPU %", 0.18),
            ("MEMORY %", 0.24)
        ]

        header = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=8)
        header.pack(fill="x", padx=7, pady=(7, 3))

        for title, _weight in headings:
            ctk.CTkLabel(
                header, text=title,
                text_color=MUTED,
                font=("Segoe UI", 10, "bold"),
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=10, pady=10)

        rows = self.process_rows

        if self.current_page == "Processes" and self.search_entry is not None:
            query = self.search_entry.get().strip().lower()
            if query:
                rows = [
                    row for row in rows
                    if query in str(row[0]).lower()
                    or query in row[1].lower()
                ]

        if limit is not None:
            rows = rows[:limit]

        if not rows:
            ctk.CTkLabel(
                parent,
                text="No processes available yet.",
                text_color=MUTED,
                font=("Segoe UI", 11)
            ).pack(anchor="w", padx=14, pady=16)
            return

        for index, (pid, name, cpu, ram) in enumerate(rows):
            row_frame = ctk.CTkFrame(
                parent,
                fg_color=CARD if index % 2 == 0 else "#162238",
                corner_radius=6
            )
            row_frame.pack(fill="x", padx=7, pady=2)

            values = [str(pid), name[:45], f"{cpu:.1f}", f"{ram:.2f}"]

            for value in values:
                ctk.CTkLabel(
                    row_frame, text=value,
                    text_color=TEXT,
                    font=("Segoe UI", 11),
                    anchor="w"
                ).pack(side="left", fill="x", expand=True, padx=10, pady=9)

    def read_processes(self):
        processes = []

        for proc in psutil.process_iter():
            try:
                pid = proc.pid
                name = proc.name() or "Unknown"
                memory = proc.memory_percent()
                cpu = proc.cpu_percent(interval=None)

                processes.append((pid, name, cpu, memory))

            except (
                psutil.AccessDenied,
                psutil.NoSuchProcess,
                psutil.ZombieProcess,
                OSError
            ):
                continue

        processes.sort(key=lambda item: item[3], reverse=True)
        return processes

    def refresh_processes(self):
        if self.closing:
            return

        try:
            self.process_rows = self.read_processes()

            if self.current_page == "Overview" and self.top_process_frame is not None:
                self.draw_process_table(self.top_process_frame, limit=5)

            elif self.current_page == "Processes" and self.process_table_frame is not None:
                self.draw_process_table(self.process_table_frame)

        except (psutil.Error, OSError) as error:
            if self.alert_label is not None:
                self.alert_label.configure(
                    text=f"●  Process scan issue: {error}",
                    text_color=ORANGE
                )

        if not self.closing:
            self.process_job = self.after(
                PROCESS_REFRESH_MS, self.refresh_processes
            )

    # ---------------- LIVE METRICS ----------------

    def update_metrics(self):
        if self.closing:
            return

        try:
            cpu = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            ram = memory.percent
            disk = psutil.disk_usage("C:\\")

            self.cpu_history.append(cpu)
            self.ram_history.append(ram)

            self.cpu_history = self.cpu_history[-HISTORY_SIZE:]
            self.ram_history = self.ram_history[-HISTORY_SIZE:]

            if self.metric_widgets:
                value, detail, progress = self.metric_widgets["cpu"]
                value.configure(text=f"{cpu:.1f}%")
                detail.configure(
                    text=f"{psutil.cpu_count(logical=True)} logical cores"
                )
                progress.set(min(cpu / 100, 1))

                value, detail, progress = self.metric_widgets["ram"]
                value.configure(text=f"{ram:.1f}%")
                detail.configure(
                    text=f"{memory.used / 1024**3:.1f} GB used / "
                         f"{memory.total / 1024**3:.1f} GB"
                )
                progress.set(min(ram / 100, 1))

                value, detail, progress = self.metric_widgets["disk"]
                value.configure(text=f"{disk.percent:.1f}%")
                detail.configure(text=f"{disk.free / 1024**3:.1f} GB free")
                progress.set(min(disk.percent / 100, 1))

            warnings = []
            if cpu >= CPU_ALERT:
                warnings.append(f"High CPU: {cpu:.1f}%")
            if ram >= RAM_ALERT:
                warnings.append(f"High RAM: {ram:.1f}%")

            if self.alert_label is not None:
                if warnings:
                    self.alert_label.configure(
                        text="●  " + "   |   ".join(warnings),
                        text_color=RED
                    )
                else:
                    self.alert_label.configure(
                        text="●  All systems operating normally",
                        text_color=GREEN
                    )

            if "cpu" in self.graphs:
                self.update_graph(self.graphs["cpu"], self.cpu_history, cpu)
                self.update_graph(self.graphs["ram"], self.ram_history, ram)

            if "cpu_large" in self.graphs:
                self.update_graph(
                    self.graphs["cpu_large"], self.cpu_history, cpu
                )
                self.update_graph(
                    self.graphs["ram_large"], self.ram_history, ram
                )

            self.clock_label.configure(
                text=datetime.now().strftime("%d %b %Y  •  %I:%M:%S %p")
            )

        except KeyboardInterrupt:
            self.close_app()
            return

        except (psutil.Error, OSError) as error:
            if self.alert_label is not None:
                self.alert_label.configure(
                    text=f"●  System data unavailable: {error}",
                    text_color=RED
                )

        except Exception as error:
            if self.alert_label is not None:
                self.alert_label.configure(
                    text=f"●  Update issue: {error}",
                    text_color=ORANGE
                )

        if not self.closing:
            self.metric_job = self.after(
                REFRESH_MS, self.update_metrics
            )

    # ---------------- ABOUT ----------------

    def build_about_page(self):
        panel = ctk.CTkFrame(
            self.content, fg_color=CARD,
            corner_radius=16, border_width=1,
            border_color=BORDER
        )
        panel.pack(fill="x", pady=10)

        ctk.CTkLabel(
            panel, text="SystemScope",
            text_color=CYAN,
            font=("Segoe UI", 28, "bold")
        ).pack(anchor="w", padx=24, pady=(24, 8))

        ctk.CTkLabel(
            panel,
            text="A lightweight Windows PC health monitor.",
            text_color=TEXT,
            font=("Segoe UI", 14)
        ).pack(anchor="w", padx=24, pady=(0, 18))

        details = [
            "• Live CPU, RAM and C: drive usage",
            "• CPU and memory performance history",
            "• Processes ranked by memory usage",
            "• Process name and PID search",
            "• High CPU/RAM threshold alerts",
            "• Safe handling of protected processes",
            "",
            "Built with Python, CustomTkinter, psutil and Matplotlib.",
            "Note: process CPU percentages may exceed 100% on multi-core systems."
        ]

        for line in details:
            ctk.CTkLabel(
                panel, text=line,
                text_color=MUTED,
                font=("Segoe UI", 12),
                justify="left"
            ).pack(anchor="w", padx=24, pady=3)

        ctk.CTkLabel(panel, text="", height=18).pack()

    # ---------------- SHUTDOWN ----------------

    def close_app(self):
        if self.closing:
            return

        self.closing = True

        for job in (self.metric_job, self.process_job):
            if job is not None:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass

        try:
            self.destroy()
        except tk.TclError:
            pass


if __name__ == "__main__":
    app = SystemScope()
    app.mainloop()