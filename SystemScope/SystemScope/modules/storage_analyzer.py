import csv
import os
import threading
from datetime import datetime
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

from utils.file_tools import find_duplicate_groups


TEMP_EXTENSIONS = {".tmp", ".temp", ".bak", ".old", ".dmp", ".chk", ".partial"}
TEMP_NAME_HINTS = ("temp", "cache", "crash", "dump")
SKIP_DIRS = {"$RECYCLE.BIN", "System Volume Information", "node_modules", ".git", "__pycache__"}


def format_size(size):
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:,.1f} {unit}"
        value /= 1024


class StorageAnalyzer(ctk.CTkFrame):
    """Read-only storage analysis. Cleanup is preview-only; no files are deleted."""

    def __init__(self, master):
        super().__init__(master, fg_color="#0b1120")
        self.folder = None
        self.busy = False
        self.file_records = []
        self.last_scan_at = None
        self.last_view = "ready"

        ctk.CTkLabel(
            self, text="Storage Intelligence",
            font=ctk.CTkFont(size=27, weight="bold"), text_color="#f8fafc"
        ).pack(anchor="w", padx=24, pady=(20, 3))
        ctk.CTkLabel(
            self, text="Find large files, exact duplicates and potential cleanup candidates",
            text_color="#94a3b8"
        ).pack(anchor="w", padx=26, pady=(0, 12))

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=22, pady=(0, 4))
        ctk.CTkButton(toolbar, text="Choose Folder", command=self.choose_folder).pack(side="left", padx=(0, 8))
        self.scan_button = ctk.CTkButton(toolbar, text="Scan Storage", command=self.scan)
        self.scan_button.pack(side="left", padx=(0, 8))
        self.duplicate_button = ctk.CTkButton(
            toolbar, text="Find Exact Duplicates", command=self.find_duplicates,
            fg_color="#334155", hover_color="#475569"
        )
        self.duplicate_button.pack(side="left", padx=(0, 8))
        self.cleanup_button = ctk.CTkButton(
            toolbar, text="Cleanup Preview", command=self.cleanup_preview,
            fg_color="#854d0e", hover_color="#a16207"
        )
        self.cleanup_button.pack(side="left", padx=(0, 8))
        self.export_button = ctk.CTkButton(
            toolbar, text="Export CSV", command=self.export_csv,
            fg_color="#334155", hover_color="#475569"
        )
        self.export_button.pack(side="left")

        self.path_label = ctk.CTkLabel(self, text="No folder selected", text_color="#94a3b8", anchor="w")
        self.path_label.pack(fill="x", padx=27, pady=(8, 4))
        self.status = ctk.CTkLabel(
            self, text="Choose a folder, then scan. This module does not delete or move files.",
            text_color="#94a3b8", anchor="w"
        )
        self.status.pack(fill="x", padx=27, pady=(0, 8))
        self.output = ctk.CTkTextbox(self, fg_color="#111c2f", text_color="#dbeafe", font=("Consolas", 11))
        self.output.pack(fill="both", expand=True, padx=25, pady=(0, 18))
        self._show_text(
            "STORAGE INTELLIGENCE\n" + "=" * 76 +
            "\n\n1. Choose a folder you want to inspect.\n"
            "2. Scan Storage finds the largest files and summarizes extension usage.\n"
            "3. Find Exact Duplicates compares same-size files with SHA-256.\n"
            "4. Cleanup Preview only lists likely temporary files for your review.\n\n"
            "SAFETY: No files are automatically deleted, moved, or modified.\n"
        )

    def _show_text(self, text):
        if not self.winfo_exists():
            return
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("end", text)
        self.output.configure(state="disabled")

    def choose_folder(self):
        selected = filedialog.askdirectory(parent=self.winfo_toplevel())
        if selected:
            self.folder = Path(selected)
            self.file_records = []
            self.path_label.configure(text=str(self.folder))
            self.status.configure(text="Folder selected. Run Scan Storage first.")
            self._show_text("Selected folder:\n" + str(self.folder) + "\n\nNo files have been modified.")

    def _set_busy(self, busy, status=None):
        self.busy = busy
        state = "disabled" if busy else "normal"
        for button in (self.scan_button, self.duplicate_button, self.cleanup_button, self.export_button):
            button.configure(state=state)
        if status:
            self.status.configure(text=status)

    def scan(self):
        if not self.folder:
            messagebox.showinfo("Choose a folder", "Choose a folder first.", parent=self.winfo_toplevel())
            return
        if self.busy:
            return
        self._set_busy(True, "Scanning files and calculating storage totals...")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        records, errors = [], 0
        extension_sizes, extension_counts = {}, {}
        total_size = 0
        try:
            def on_error(_error):
                nonlocal errors
                errors += 1

            for root, dirs, filenames in os.walk(self.folder, onerror=on_error, followlinks=False):
                dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
                for filename in filenames:
                    path = Path(root) / filename
                    try:
                        if path.is_symlink():
                            continue
                        stat = path.stat()
                        record = {"path": str(path), "name": path.name, "size": stat.st_size,
                                  "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                                  "extension": path.suffix.lower() or "[no extension]"}
                        records.append(record)
                        total_size += stat.st_size
                        extension_sizes[record["extension"]] = extension_sizes.get(record["extension"], 0) + stat.st_size
                        extension_counts[record["extension"]] = extension_counts.get(record["extension"], 0) + 1
                    except OSError:
                        errors += 1

            records.sort(key=lambda item: item["size"], reverse=True)
            lines = [
                "STORAGE SCAN REPORT", "=" * 82,
                f"Folder: {self.folder}", f"Scanned at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Readable files: {len(records):,}", f"Combined file size: {format_size(total_size)}",
                f"Unreadable/skipped items: {errors:,}", "",
                "TOP 50 LARGEST FILES", "-" * 82
            ]
            lines.extend(f"{format_size(item['size']):>12}  {item['path']}" for item in records[:50])
            lines += ["", "STORAGE BY FILE EXTENSION", "-" * 82]
            for ext, size in sorted(extension_sizes.items(), key=lambda pair: pair[1], reverse=True)[:30]:
                lines.append(f"{ext:<20} {extension_counts[ext]:>7,} files  {format_size(size):>12}")
            if not records:
                lines.append("No readable files found.")
            report = "\n".join(lines)
            self.after(0, lambda: self._finish_scan(records, report, len(records), total_size, errors))
        except Exception as error:
            message = f"Storage scan failed: {error}"
            try:
                self.after(0, lambda message=message: self._finish_error(message))
            except RuntimeError:
                pass

    def _finish_scan(self, records, report, count, total_size, errors):
        if not self.winfo_exists():
            return
        self.file_records = records
        self.last_scan_at = datetime.now().isoformat(timespec="seconds")
        self.last_view = "scan"
        self._show_text(report)
        self._set_busy(False, f"Scan complete | {count:,} files | {format_size(total_size)} | {errors} errors/skips")

    def _finish_error(self, message):
        if not self.winfo_exists():
            return
        self._show_text(message)
        self._set_busy(False, "Scan failed. Check folder permissions and try again.")

    def find_duplicates(self):
        if self.busy:
            return
        if not self.file_records:
            messagebox.showinfo("Scan first", "Run Scan Storage first so duplicate detection can use its file inventory.", parent=self.winfo_toplevel())
            return
        self._set_busy(True, "Checking same-size files with SHA-256. Large folders may take time...")
        threading.Thread(target=self._duplicates_worker, daemon=True).start()

    def _duplicates_worker(self):
        try:
            groups = find_duplicate_groups(self.file_records)
            lines = ["EXACT DUPLICATE FILES", "=" * 82,
                     "Duplicates have matching sizes and SHA-256 hashes.",
                     "Review each group manually before removing anything.", ""]
            wasted = 0
            duplicate_files = 0
            for index, group in enumerate(groups, start=1):
                wasted += group[0]["size"] * (len(group) - 1)
                duplicate_files += len(group) - 1
                lines.append(f"GROUP {index} | {len(group)} copies | each {format_size(group[0]['size'])}")
                for item in group:
                    lines.append(f"    {item['path']}")
                lines.append("")
            if not groups:
                lines.append("No exact duplicate groups found in readable files.")
            lines += ["", f"Duplicate copies (beyond one per group): {duplicate_files:,}",
                      f"Potential reclaimable space: {format_size(wasted)}", "",
                      "NOTE: Hash matches indicate identical file content, not that a file is safe to delete."]
            report = "\n".join(lines)
            self.after(0, lambda: self._finish_operation(report, f"Duplicate check complete | {len(groups)} groups | potential duplicate space {format_size(wasted)}", "duplicates"))
        except Exception as error:
            message = f"Duplicate scan failed: {error}"
            try:
                self.after(0, lambda message=message: self._finish_error(message))
            except RuntimeError:
                pass

    def cleanup_preview(self):
        if not self.file_records:
            messagebox.showinfo("Scan first", "Run Scan Storage first to build a file inventory.", parent=self.winfo_toplevel())
            return
        candidates = []
        for item in self.file_records:
            path = Path(item["path"])
            lower_name = path.name.lower()
            if path.suffix.lower() in TEMP_EXTENSIONS or any(hint in lower_name for hint in TEMP_NAME_HINTS):
                candidates.append(item)
        candidates.sort(key=lambda item: item["size"], reverse=True)
        total = sum(item["size"] for item in candidates)
        lines = ["CLEANUP CANDIDATE PREVIEW", "=" * 82,
                 "Heuristic list only: names/extensions can be misleading.",
                 "Nothing will be deleted or changed by this preview.", "",
                 f"Candidates: {len(candidates):,}", f"Combined size: {format_size(total)}", ""]
        lines.extend(f"{format_size(item['size']):>12}  {item['path']}" for item in candidates[:500])
        if not candidates:
            lines.append("No likely temporary/cache files were found by the current rules.")
        if len(candidates) > 500:
            lines.append(f"\nOnly first 500 of {len(candidates):,} candidates displayed.")
        self._finish_operation("\n".join(lines), f"Cleanup preview | {len(candidates):,} candidates | no files changed", "cleanup")

    def _finish_operation(self, report, status, view):
        if not self.winfo_exists():
            return
        self.last_view = view
        self._show_text(report)
        self._set_busy(False, status)

    def export_csv(self):
        if not self.file_records:
            messagebox.showinfo("Nothing to export", "Run Scan Storage first to create a file inventory.", parent=self.winfo_toplevel())
            return
        target = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(), title="Export storage inventory",
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
            initialfile="systemscope_storage_inventory.csv"
        )
        if not target:
            return
        try:
            with open(target, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.DictWriter(file, fieldnames=["name", "path", "size", "modified", "extension"])
                writer.writeheader()
                writer.writerows(self.file_records)
            messagebox.showinfo("Export complete", f"Exported {len(self.file_records):,} file records to:\n{target}", parent=self.winfo_toplevel())
        except OSError as error:
            messagebox.showerror("Export failed", str(error), parent=self.winfo_toplevel())
