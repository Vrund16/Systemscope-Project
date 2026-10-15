
import customtkinter as ctk
import psutil

from collections import deque
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class SystemMonitor(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#0b1120")

        self.cpu_history = deque(maxlen=60)
        self.ram_history = deque(maxlen=60)
        self.alive = True

        ctk.CTkLabel(
            self, text="System Monitor",
            font=ctk.CTkFont(size=27, weight="bold")
        ).pack(anchor="w", padx=24, pady=(20, 3))

        ctk.CTkLabel(
            self, text="Live performance and running processes",
            text_color="#94a3b8"
        ).pack(anchor="w", padx=26, pady=(0, 12))

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", padx=15)

        self.values = {}
        for name in ("CPU", "RAM", "Disk C:"):
            card = ctk.CTkFrame(
                cards, fg_color="#111c2f", corner_radius=12
            )
            card.pack(side="left", fill="x", expand=True, padx=6)

            ctk.CTkLabel(
                card, text=name, text_color="#94a3b8"
            ).pack(anchor="w", padx=12, pady=(12, 2))

            value = ctk.CTkLabel(
                card, text="Loading...",
                font=ctk.CTkFont(size=22, weight="bold")
            )
            value.pack(anchor="w", padx=12, pady=(0, 12))
            self.values[name] = value

        graph_frame = ctk.CTkFrame(
            self, fg_color="#111c2f", corner_radius=12
        )
        graph_frame.pack(fill="both", expand=True, padx=22, pady=12)

        self.figure = Figure(figsize=(7, 2.7), dpi=90)
        self.figure.patch.set_facecolor("#111c2f")
        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(
            self.figure, master=graph_frame
        )
        self.canvas.get_tk_widget().pack(
            fill="both", expand=True, padx=8, pady=8
        )

        ctk.CTkLabel(
            self, text="Top processes by memory",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=25)

        self.process_box = ctk.CTkTextbox(
            self, height=130,
            fg_color="#111c2f",
            font=("Consolas", 11)
        )
        self.process_box.pack(fill="x", padx=22, pady=(6, 18))

        psutil.cpu_percent(interval=None)
        self.after(500, self.refresh)

    def refresh(self):
        if not self.alive or not self.winfo_exists():
            return

        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent

            self.values["CPU"].configure(text=f"{cpu:.1f}%")
            self.values["RAM"].configure(text=f"{ram:.1f}%")

            try:
                disk = psutil.disk_usage("C:\\")
                self.values["Disk C:"].configure(
                    text=f"{disk.percent:.1f}% used"
                )
            except (OSError, ValueError):
                self.values["Disk C:"].configure(text="Unavailable")

            self.cpu_history.append(cpu)
            self.ram_history.append(ram)

            self.ax.clear()
            self.ax.set_facecolor("#111c2f")
            self.ax.plot(
                list(self.cpu_history), label="CPU", linewidth=2
            )
            self.ax.plot(
                list(self.ram_history), label="RAM", linewidth=2
            )
            self.ax.set_ylim(0, 100)
            self.ax.set_ylabel("Usage (%)", color="#cbd5e1")
            self.ax.tick_params(colors="#94a3b8")
            self.ax.grid(alpha=0.2)
            self.ax.legend()
            self.figure.tight_layout()
            self.canvas.draw_idle()

            processes = []
            for proc in psutil.process_iter(
                ["pid", "name", "memory_percent"]
            ):
                try:
                    info = proc.info
                    processes.append((
                        info["memory_percent"] or 0,
                        info["pid"],
                        info["name"] or "Unknown"
                    ))
                except (
                    psutil.AccessDenied,
                    psutil.NoSuchProcess,
                    psutil.ZombieProcess
                ):
                    continue

            processes.sort(reverse=True)

            self.process_box.delete("1.0", "end")
            self.process_box.insert(
                "end", f"{'PID':<9} {'RAM %':<9} PROCESS\n"
            )

            for memory, pid, name in processes[:8]:
                self.process_box.insert(
                    "end", f"{pid:<9} {memory:>5.1f}%   {name[:40]}\n"
                )

        except Exception as error:
            self.process_box.delete("1.0", "end")
            self.process_box.insert("end", f"Monitor error: {error}")

        if self.alive and self.winfo_exists():
            self.after(2000, self.refresh)

    def destroy(self):
        self.alive = False
        super().destroy()
