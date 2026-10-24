"""Low-overhead live system monitor for SystemScope."""
from collections import deque
import customtkinter as ctk
import psutil
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

BG = "#0b1120"
PANEL = "#111c2f"
MUTED = "#94a3b8"
WHITE = "#f8fafc"
BLUE = "#83a5ff"
CYAN = "#54d8d0"


class SystemMonitor(ctk.CTkFrame):
    """Refresh metrics frequently, but scan processes and redraw charts less often."""
    REFRESH_MS = 2000
    PROCESS_REFRESH_MS = 6000

    def __init__(self, master):
        super().__init__(master, fg_color=BG)
        self.alive = True
        self.refresh_job = None
        self.process_job = None
        self.cpu_history = deque(maxlen=60)
        self.ram_history = deque(maxlen=60)
        self._last_chart_len = 0
        self._build_ui()
        psutil.cpu_percent(interval=None)
        self.refresh_metrics()
        self.refresh_processes()

    def _build_ui(self):
        ctk.CTkLabel(self, text="System Monitor", text_color=WHITE,
                      font=ctk.CTkFont(size=27, weight="bold")).pack(anchor="w", padx=24, pady=(20, 3))
        ctk.CTkLabel(self, text="Live performance with staggered, low-overhead updates", text_color=MUTED).pack(anchor="w", padx=26, pady=(0, 12))

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", padx=15)
        self.values = {}
        self.system_drive = os.environ.get("SystemDrive", "C:") + "\\" if os.name == "nt" else "/"
        disk_label = f"Disk {self.system_drive[:2]}" if os.name == "nt" else "Disk /"
        for name in ("CPU", "RAM", disk_label):
            card = ctk.CTkFrame(cards, fg_color=PANEL, corner_radius=12, border_width=1, border_color="#24334d")
            card.pack(side="left", fill="x", expand=True, padx=6)
            ctk.CTkLabel(card, text=name, text_color=MUTED).pack(anchor="w", padx=12, pady=(12, 2))
            value = ctk.CTkLabel(card, text="Loading…", text_color=WHITE, font=ctk.CTkFont(size=22, weight="bold"))
            value.pack(anchor="w", padx=12, pady=(0, 12))
            self.values[name] = value

        graph_frame = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=12, border_width=1, border_color="#24334d")
        graph_frame.pack(fill="both", expand=True, padx=22, pady=12)
        self.figure = Figure(figsize=(7, 2.7), dpi=85)
        self.figure.patch.set_facecolor(PANEL)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(PANEL)
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, 59)
        self.ax.set_ylabel("Usage (%)", color=MUTED)
        self.ax.tick_params(colors=MUTED, labelsize=8)
        self.ax.grid(alpha=0.18, color="#94a3b8")
        for spine in self.ax.spines.values(): spine.set_color("#293850")
        self.cpu_line, = self.ax.plot([], [], color=BLUE, label="CPU", linewidth=1.8)
        self.ram_line, = self.ax.plot([], [], color=CYAN, label="RAM", linewidth=1.8)
        legend = self.ax.legend(facecolor=PANEL, edgecolor="#293850", labelcolor=WHITE, fontsize=8, loc="upper left")
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(self, text="Top processes by memory", text_color=WHITE,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=25)
        self.process_box = ctk.CTkTextbox(self, height=130, fg_color=PANEL, text_color="#dbeafe", font=("Consolas", 11))
        self.process_box.pack(fill="x", padx=22, pady=(6, 8))
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(footer, text="Metrics: every 2s  ·  Process inventory: every 6s", text_color=MUTED,
                     font=ctk.CTkFont(size=10)).pack(side="left")
        ctk.CTkButton(footer, text="Refresh processes", width=130, height=30,
                      command=self.refresh_processes).pack(side="right")

    def refresh_metrics(self):
        if not self.alive or not self.winfo_exists(): return
        try:
            cpu = psutil.cpu_percent(interval=0.25)
            ram = psutil.virtual_memory().percent
            self.values["CPU"].configure(text=f"{cpu:.1f}%")
            self.values["RAM"].configure(text=f"{ram:.1f}%")
            try:
                disk = psutil.disk_usage(self.system_drive)
                disk_label = next(key for key in self.values if key.startswith("Disk "))
                self.values[disk_label].configure(text=f"{disk.percent:.1f}% used")
            except (OSError, ValueError):
                disk_label = next(key for key in self.values if key.startswith("Disk "))
                self.values[disk_label].configure(text="Unavailable")
            self.cpu_history.append(cpu); self.ram_history.append(ram)
            xs = list(range(len(self.cpu_history)))
            self.cpu_line.set_data(xs, list(self.cpu_history))
            self.ram_line.set_data(xs, list(self.ram_history))
            self.ax.set_xlim(0, max(59, len(xs)-1))
            self.canvas.draw_idle()
        except (OSError, ValueError, psutil.Error) as error:
            self.process_box.delete("1.0", "end")
            self.process_box.insert("end", f"Monitor warning: {error}")
        if self.alive and self.winfo_exists(): self.refresh_job = self.after(self.REFRESH_MS, self.refresh_metrics)

    def refresh_processes(self):
        if not self.alive or not self.winfo_exists(): return
        processes = []
        try:
            for proc in psutil.process_iter(["pid", "name", "memory_percent"]):
                try:
                    info = proc.info
                    processes.append((info.get("memory_percent") or 0, info.get("pid") or 0, info.get("name") or "Unknown"))
                except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                    continue
            processes.sort(reverse=True)
            lines = [f"{'PID':<9} {'RAM %':<9} PROCESS", "-" * 58]
            lines.extend(f"{pid:<9} {memory:>5.1f}%   {name[:40]}" for memory, pid, name in processes[:8])
            self.process_box.delete("1.0", "end")
            self.process_box.insert("end", "\n".join(lines))
        except (OSError, psutil.Error) as error:
            self.process_box.delete("1.0", "end")
            self.process_box.insert("end", f"Process inventory unavailable: {error}")
        if self.alive and self.winfo_exists(): self.process_job = self.after(self.PROCESS_REFRESH_MS, self.refresh_processes)

    def destroy(self):
        self.alive = False
        for job in (self.refresh_job, self.process_job):
            if job is not None:
                try: self.after_cancel(job)
                except Exception: pass
        super().destroy()
