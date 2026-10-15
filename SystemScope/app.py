
import customtkinter as ctk
import psutil
import os
from datetime import datetime

from modules.system_monitor import SystemMonitor
from modules.file_wizard import FileWizard
from modules.storage_analyzer import StorageAnalyzer


# -------------------- THEME --------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#0b1120"
SIDEBAR = "#0f1727"
PANEL = "#111c2f"
PANEL_LIGHT = "#1b2a41"
BLUE = "#60a5fa"
GREEN = "#34d399"
AMBER = "#fbbf24"
MUTED = "#94a3b8"
WHITE = "#f8fafc"


# -------------------- MAIN APPLICATION --------------------

class SystemScopeSuite(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("SystemScope Suite")
        self.geometry("1250x800")
        self.minsize(850, 600)
        self.configure(fg_color=BG)

        self.active_module = None
        self.overview_active = False
        self.refresh_job = None
        self.last_cpu = 0

        # Warm up CPU measurement without blocking the UI.
        psutil.cpu_percent(interval=None)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(
            self,
            width=225,
            corner_radius=0,
            fg_color=SIDEBAR
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.content = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=BG
        )
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.show_overview()

        self.protocol("WM_DELETE_WINDOW", self.close_app)

    # -------------------- SIDEBAR --------------------

    def build_sidebar(self):

        ctk.CTkLabel(
            self.sidebar,
            text="SYSTEMSCOPE",
            font=ctk.CTkFont(size=23, weight="bold"),
            text_color=BLUE
        ).pack(anchor="w", padx=20, pady=(28, 2))

        ctk.CTkLabel(
            self.sidebar,
            text="PC UTILITY SUITE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=MUTED
        ).pack(anchor="w", padx=21, pady=(0, 28))

        ctk.CTkLabel(
            self.sidebar,
            text="WORKSPACE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#64748b"
        ).pack(anchor="w", padx=20, pady=(0, 8))

        navigation = [
            ("⌂   Overview", self.show_overview),
            ("▥   System Monitor", self.show_system),
            ("▤   FileWizard", self.show_files),
            ("▦   Storage Analyzer", self.show_storage),
        ]

        self.nav_buttons = []

        for label, command in navigation:

            button = ctk.CTkButton(
                self.sidebar,
                text=label,
                command=command,
                anchor="w",
                height=43,
                corner_radius=9,
                fg_color="transparent",
                hover_color=PANEL_LIGHT,
                text_color="#dbe5f4",
                font=ctk.CTkFont(size=13)
            )

            button.pack(fill="x", padx=12, pady=4)
            self.nav_buttons.append(button)

        ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color="#253248"
        ).pack(fill="x", padx=18, pady=20)

        ctk.CTkLabel(
            self.sidebar,
            text="SYSTEM STATUS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#64748b"
        ).pack(anchor="w", padx=20)

        ctk.CTkLabel(
            self.sidebar,
            text="●  Local monitoring active",
            text_color=GREEN,
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=20, pady=(10, 3))

        ctk.CTkLabel(
            self.sidebar,
            text="Version 1.0 | Windows",
            text_color="#64748b",
            font=ctk.CTkFont(size=10)
        ).pack(side="bottom", anchor="w", padx=20, pady=20)

    # -------------------- PAGE MANAGEMENT --------------------

    def clear_page(self):

        self.overview_active = False

        if self.refresh_job is not None:
            try:
                self.after_cancel(self.refresh_job)
            except Exception:
                pass

            self.refresh_job = None

        if self.active_module is not None:
            try:
                self.active_module.destroy()
            except Exception:
                pass

            self.active_module = None

        for widget in self.content.winfo_children():
            widget.destroy()

    def page_heading(self, parent, title, subtitle):

        ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=WHITE
        ).pack(anchor="w", padx=24, pady=(18, 2))

        ctk.CTkLabel(
            parent,
            text=subtitle,
            font=ctk.CTkFont(size=13),
            text_color=MUTED
        ).pack(anchor="w", padx=26, pady=(0, 18))

    # -------------------- DASHBOARD CARDS --------------------

    def make_card(self, parent, title, accent):

        card = ctk.CTkFrame(
            parent,
            fg_color=PANEL,
            corner_radius=14,
            border_width=1,
            border_color="#1e2b40"
        )

        ctk.CTkLabel(
            card,
            text=title.upper(),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=MUTED
        ).pack(anchor="w", padx=15, pady=(14, 4))

        value = ctk.CTkLabel(
            card,
            text="--",
            font=ctk.CTkFont(size=27, weight="bold"),
            text_color=accent
        )
        value.pack(anchor="w", padx=15, pady=(0, 3))

        detail = ctk.CTkLabel(
            card,
            text="Collecting data...",
            font=ctk.CTkFont(size=11),
            text_color=MUTED,
            wraplength=260
        )
        detail.pack(anchor="w", padx=15, pady=(0, 12))

        return card, value, detail

    # -------------------- OVERVIEW --------------------

    def show_overview(self):

        self.clear_page()
        self.overview_active = True

        # Scrollable dashboard
        self.dashboard = ctk.CTkScrollableFrame(
            self.content,
            fg_color=BG,
            corner_radius=0
        )
        self.dashboard.pack(fill="both", expand=True)

        self.page_heading(
            self.dashboard,
            "Overview",
            "Your PC at a glance. Monitor resources and manage your files."
        )

        # Responsive metrics grid
        self.metrics_grid = ctk.CTkFrame(
            self.dashboard,
            fg_color="transparent"
        )
        self.metrics_grid.pack(fill="x", padx=20, pady=(0, 15))

        self.metrics_grid.grid_columnconfigure(
            (0, 1, 2),
            weight=1,
            uniform="metrics"
        )

        specs = [
            ("CPU Usage", BLUE),
            ("Memory Usage", GREEN),
            ("Disk Usage", AMBER)
        ]

        self.metric_values = {}
        self.metric_details = {}
        self.metric_cards = []

        for column, (title, accent) in enumerate(specs):

            card, value, detail = self.make_card(
                self.metrics_grid,
                title,
                accent
            )

            card.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=5,
                pady=4
            )

            self.metric_values[title] = value
            self.metric_details[title] = detail
            self.metric_cards.append(card)

        # Resource utilization panel
        self.resource_panel = ctk.CTkFrame(
            self.dashboard,
            fg_color=PANEL,
            corner_radius=14
        )
        self.resource_panel.pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkLabel(
            self.resource_panel,
            text="RESOURCE UTILIZATION",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=WHITE
        ).pack(anchor="w", padx=17, pady=(14, 8))

        self.bars = {}

        for name in ("CPU", "RAM", "Disk"):

            line = ctk.CTkFrame(
                self.resource_panel,
                fg_color="transparent"
            )
            line.pack(fill="x", padx=17, pady=6)

            ctk.CTkLabel(
                line,
                text=name,
                width=45,
                anchor="w",
                text_color=MUTED
            ).pack(side="left")

            bar = ctk.CTkProgressBar(
                line,
                height=9,
                progress_color=BLUE
            )
            bar.pack(side="left", fill="x", expand=True, padx=10)
            bar.set(0)

            percent = ctk.CTkLabel(
                line,
                text="0%",
                width=55,
                anchor="e",
                text_color=WHITE
            )
            percent.pack(side="right")

            self.bars[name] = (bar, percent)

        # Quick access
        ctk.CTkLabel(
            self.dashboard,
            text="QUICK ACCESS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=WHITE
        ).pack(anchor="w", padx=25, pady=(2, 8))

        self.quick_grid = ctk.CTkFrame(
            self.dashboard,
            fg_color="transparent"
        )
        self.quick_grid.pack(fill="x", padx=20)

        self.quick_grid.grid_columnconfigure(
            (0, 1, 2),
            weight=1,
            uniform="quick"
        )

        quick_actions = [
            (
                "System Monitor",
                "Live performance and processes",
                self.show_system
            ),
            (
                "FileWizard",
                "Browse, search and rename files",
                self.show_files
            ),
            (
                "Storage Analyzer",
                "Inspect folders and find large files",
                self.show_storage
            )
        ]

        self.quick_cards = []

        for column, (title, description, command) in enumerate(
            quick_actions
        ):

            card = ctk.CTkFrame(
                self.quick_grid,
                fg_color=PANEL,
                corner_radius=12
            )

            card.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=5,
                pady=4
            )

            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=WHITE
            ).pack(anchor="w", padx=12, pady=(13, 3))

            ctk.CTkLabel(
                card,
                text=description,
                font=ctk.CTkFont(size=11),
                text_color=MUTED,
                wraplength=210,
                justify="left"
            ).pack(anchor="w", padx=12, pady=(0, 10))

            ctk.CTkButton(
                card,
                text="Open →",
                command=command,
                height=32
            ).pack(fill="x", padx=12, pady=(0, 12))

            self.quick_cards.append(card)

        # System snapshot
        self.snapshot_panel = ctk.CTkFrame(
            self.dashboard,
            fg_color=PANEL,
            corner_radius=12
        )
        self.snapshot_panel.pack(fill="x", padx=25, pady=15)

        ctk.CTkLabel(
            self.snapshot_panel,
            text="SYSTEM SNAPSHOT",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=WHITE
        ).pack(anchor="w", padx=16, pady=(12, 3))

        self.snapshot = ctk.CTkLabel(
            self.snapshot_panel,
            text="Collecting system information...",
            text_color=MUTED,
            justify="left",
            wraplength=850
        )
        self.snapshot.pack(anchor="w", padx=16, pady=(0, 12))

        # Responsive layout on window resize
        self.bind("<Configure>", self.handle_resize)

        self.refresh_overview()

    # -------------------- RESPONSIVE LAYOUT --------------------

    def handle_resize(self, event):

        if event.widget != self:
            return

        if not hasattr(self, "metrics_grid"):
            return

        width = event.width - 225

        if width < 780:
            columns = 1
        elif width < 1050:
            columns = 2
        else:
            columns = 3

        self.metrics_grid.grid_columnconfigure(
            (0, 1, 2), weight=0, uniform=""
        )
        self.quick_grid.grid_columnconfigure(
            (0, 1, 2), weight=0, uniform=""
        )

        for column in range(3):
            self.metrics_grid.grid_columnconfigure(
                column,
                weight=1 if column < columns else 0,
                uniform="metrics" if column < columns else ""
            )
            self.quick_grid.grid_columnconfigure(
                column,
                weight=1 if column < columns else 0,
                uniform="quick" if column < columns else ""
            )

        for index, card in enumerate(self.metric_cards):
            card.grid_configure(
                row=index // columns,
                column=index % columns
            )

        for index, card in enumerate(self.quick_cards):
            card.grid_configure(
                row=index // columns,
                column=index % columns
            )

    # -------------------- LIGHTWEIGHT LIVE REFRESH --------------------

    def refresh_overview(self):

        if not self.overview_active or not self.winfo_exists():
            return

        try:
            # These readings are quick and non-blocking.
            cpu = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()

            self.metric_values["CPU Usage"].configure(
                text=f"{cpu:.1f}%"
            )
            self.metric_details["CPU Usage"].configure(
                text=f"{psutil.cpu_count(logical=True)} logical processors"
            )

            ram = memory.percent

            self.metric_values["Memory Usage"].configure(
                text=f"{ram:.1f}%"
            )
            self.metric_details["Memory Usage"].configure(
                text=f"{memory.used / (1024**3):.1f} GB used of "
                     f"{memory.total / (1024**3):.1f} GB"
            )

            disk_percent = 0

            try:
                disk = psutil.disk_usage(os.environ.get("SystemDrive", "C:") + "\\")
                disk_percent = disk.percent

                self.metric_values["Disk Usage"].configure(
                    text=f"{disk_percent:.1f}%"
                )
                self.metric_details["Disk Usage"].configure(
                    text=f"{disk.free / (1024**3):.1f} GB free"
                )

            except (OSError, ValueError):
                self.metric_values["Disk Usage"].configure(text="N/A")
                self.metric_details["Disk Usage"].configure(
                    text="Drive unavailable"
                )

            values = {
                "CPU": cpu,
                "RAM": ram,
                "Disk": disk_percent
            }

            for name, percentage in values.items():

                bar, label = self.bars[name]

                bar.set(max(0, min(100, percentage)) / 100)
                label.configure(text=f"{percentage:.1f}%")

            # Avoid scanning every process every refresh.
            # Process count is updated only once every 15 seconds.
            now = datetime.now()

            if (
                not hasattr(self, "last_process_count_time")
                or (now - self.last_process_count_time).total_seconds() >= 15
            ):
                self.cached_process_count = len(psutil.pids())
                self.last_process_count_time = now

            boot = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot

            self.snapshot.configure(
                text=(
                    f"System uptime: {str(uptime).split('.')[0]}   |   "
                    f"Running processes: "
                    f"{getattr(self, 'cached_process_count', '--')}   |   "
                    f"Last refreshed: {now:%H:%M:%S}"
                )
            )

        except Exception as error:
            try:
                self.snapshot.configure(
                    text=f"Unable to refresh system information: {error}"
                )
            except Exception:
                pass

        if self.overview_active:
            self.refresh_job = self.after(
                3000,
                self.refresh_overview
            )
        else:
            self.refresh_job = None

    # -------------------- MODULES --------------------

    def show_system(self):

        self.clear_page()

        self.active_module = SystemMonitor(self.content)
        self.active_module.pack(fill="both", expand=True)

    def show_files(self):

        self.clear_page()

        self.active_module = FileWizard(self.content)
        self.active_module.pack(fill="both", expand=True)

    def show_storage(self):

        self.clear_page()

        self.active_module = StorageAnalyzer(self.content)
        self.active_module.pack(fill="both", expand=True)

    # -------------------- CLEAN EXIT --------------------

    def close_app(self):

        self.overview_active = False

        if self.refresh_job is not None:
            try:
                self.after_cancel(self.refresh_job)
            except Exception:
                pass

        self.destroy()


# -------------------- RUN APPLICATION --------------------

if __name__ == "__main__":
    app = SystemScopeSuite()
    app.mainloop()
