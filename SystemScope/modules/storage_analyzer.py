
import os
import threading
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox


def format_size(size):
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:,.1f} {unit}"
        value /= 1024


class StorageAnalyzer(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#0b1120")
        self.folder = None
        self.busy = False

        ctk.CTkLabel(
            self, text="Storage Analyzer",
            font=ctk.CTkFont(size=27, weight="bold")
        ).pack(anchor="w", padx=24, pady=(20, 3))

        ctk.CTkLabel(
            self, text="Find large files and inspect folder storage",
            text_color="#94a3b8"
        ).pack(anchor="w", padx=26, pady=(0, 12))

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=22)

        ctk.CTkButton(
            toolbar, text="Choose Folder",
            command=self.choose_folder
        ).pack(side="left", padx=(0, 8))

        self.scan_button = ctk.CTkButton(
            toolbar, text="Scan Largest Files",
            command=self.scan
        )
        self.scan_button.pack(side="left")

        self.path_label = ctk.CTkLabel(
            self, text="No folder selected",
            text_color="#94a3b8"
        )
        self.path_label.pack(anchor="w", padx=27, pady=10)

        self.status = ctk.CTkLabel(
            self, text="Choose a folder to begin.",
            text_color="#94a3b8"
        )
        self.status.pack(anchor="w", padx=27, pady=(0, 8))

        self.output = ctk.CTkTextbox(
            self, fg_color="#111c2f", font=("Consolas", 11)
        )
        self.output.pack(fill="both", expand=True, padx=25, pady=(0, 18))

    def choose_folder(self):
        selected = filedialog.askdirectory()
        if selected:
            self.folder = Path(selected)
            self.path_label.configure(text=str(self.folder))
            self.output.delete("1.0", "end")
            self.output.insert("end", "Ready. No files will be modified.")

    def scan(self):
        if not self.folder:
            messagebox.showinfo("Notice", "Choose a folder first.")
            return
        if self.busy:
            return

        self.busy = True
        self.scan_button.configure(state="disabled")
        self.status.configure(text="Scanning folder... please wait.")
        threading.Thread(target=self.scan_worker, daemon=True).start()

    def scan_worker(self):
        found = []
        total_size = 0
        count = 0
        errors = 0

        try:
            def on_error(_error):
                nonlocal errors
                errors += 1

            for root, dirs, filenames in os.walk(
                self.folder, onerror=on_error
            ):
                dirs[:] = [
                    name for name in dirs
                    if name not in {
                        "$RECYCLE.BIN", "System Volume Information"
                    }
                ]

                for filename in filenames:
                    path = Path(root) / filename
                    try:
                        size = path.stat().st_size
                        total_size += size
                        count += 1
                        found.append((size, str(path)))
                    except OSError:
                        errors += 1

            found.sort(reverse=True)
            lines = [
                f"Files scanned: {count:,}",
                f"Total file size: {format_size(total_size)}",
                f"Unreadable items skipped: {errors}",
                "",
                "TOP 50 LARGEST FILES",
                "-" * 75
            ]

            for size, path in found[:50]:
                lines.append(f"{format_size(size):>12}  {path}")

            if not found:
                lines.append("No readable files found.")

            result = "\n".join(lines)

        except Exception as error:
            result = f"Scan failed: {error}"

        try:
            self.after(
                0, lambda: self.finish_scan(result, count, total_size)
            )
        except RuntimeError:
            pass

    def finish_scan(self, result, count, total_size):
        if not self.winfo_exists():
            return

        self.output.delete("1.0", "end")
        self.output.insert("end", result)
        self.status.configure(
            text=f"Finished | {count:,} files | {format_size(total_size)}"
        )
        self.scan_button.configure(state="normal")
        self.busy = False
