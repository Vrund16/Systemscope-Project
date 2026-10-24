
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox


CATEGORIES = {
    ".pdf": "Documents", ".doc": "Documents",
    ".docx": "Documents", ".txt": "Documents",
    ".csv": "Documents", ".xlsx": "Documents",
    ".jpg": "Images", ".jpeg": "Images",
    ".png": "Images", ".gif": "Images",
    ".webp": "Images", ".bmp": "Images",
    ".mp4": "Videos", ".mov": "Videos",
    ".mkv": "Videos", ".avi": "Videos",
    ".mp3": "Audio", ".wav": "Audio",
    ".zip": "Archives", ".rar": "Archives",
    ".7z": "Archives"
}


class FileWizard(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#0b1120")

        self.folder = None
        self.files = []
        self.preview_window = None
        self.rename_window = None

        ctk.CTkLabel(
            self, text="FileWizard",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#f8fafc"
        ).pack(anchor="w", padx=24, pady=(20, 3))

        ctk.CTkLabel(
            self, text="Browse, search and manage your files",
            text_color="#94a3b8"
        ).pack(anchor="w", padx=26, pady=(0, 12))

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=22)

        ctk.CTkButton(
            toolbar, text="Choose Folder",
            command=self.choose_folder
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            toolbar, text="Preview Organization",
            command=self.preview_organization
        ).pack(side="left")

        self.path_label = ctk.CTkLabel(
            self, text="No folder selected",
            text_color="#94a3b8", anchor="w"
        )
        self.path_label.pack(fill="x", padx=27, pady=10)

        self.search = ctk.CTkEntry(
            self, placeholder_text="Search by filename or extension..."
        )
        self.search.pack(fill="x", padx=25, pady=5)
        self.search.bind("<KeyRelease>", lambda _event: self.render())

        ctk.CTkButton(
            self, text="Batch Rename — Add Prefix",
            fg_color="#334155", hover_color="#475569",
            command=self.batch_rename
        ).pack(anchor="w", padx=25, pady=8)

        self.status = ctk.CTkLabel(
            self, text="Choose a folder to start.",
            text_color="#94a3b8"
        )
        self.status.pack(anchor="w", padx=27, pady=3)

        self.output = ctk.CTkTextbox(
            self, fg_color="#111c2f",
            text_color="#dbeafe", font=("Consolas", 11)
        )
        self.output.pack(
            fill="both", expand=True, padx=25, pady=(5, 18)
        )
        self.render()

    def choose_folder(self):
        selected = filedialog.askdirectory(parent=self.winfo_toplevel())
        if selected:
            self.folder = Path(selected)
            self.path_label.configure(text=str(self.folder))
            self.render()

    def render(self):
        self.output.delete("1.0", "end")

        if not self.folder:
            self.output.insert("end", "Choose a folder to view its files.")
            return

        try:
            self.files = sorted(
                [p for p in self.folder.iterdir() if p.is_file()],
                key=lambda p: p.name.lower()
            )

            query = self.search.get().strip().lower()
            matches = [p for p in self.files if query in p.name.lower()]

            self.output.insert(
                "end", f"Showing {min(len(matches), 1000)} of "
                       f"{len(matches)} matching files\n\n"
            )

            for path in matches[:1000]:
                try:
                    size = path.stat().st_size
                    size_text = f"{size:,} bytes"
                except OSError:
                    size_text = "Size unavailable"

                self.output.insert(
                    "end", f"{size_text:>18}   {path.name}\n"
                )

            self.status.configure(
                text=f"{len(self.files)} files in selected folder"
            )

        except OSError as error:
            self.status.configure(text="Could not read this folder.")
            self.output.insert("end", f"Folder error: {error}")

    def preview_organization(self):
        if not self.folder:
            messagebox.showinfo(
                "Choose a folder", "Choose a folder first.",
                parent=self.winfo_toplevel()
            )
            return

        if self.preview_window is not None:
            try:
                if self.preview_window.winfo_exists():
                    self.preview_window.lift()
                    return
            except Exception:
                pass

        window = ctk.CTkToplevel(self.winfo_toplevel())
        self.preview_window = window
        window.title("File Organization Preview")
        window.geometry("760x520")
        window.minsize(550, 350)

        ctk.CTkLabel(
            window, text="ORGANIZATION PREVIEW",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", padx=16, pady=(16, 3))

        ctk.CTkLabel(
            window,
            text="Preview only — no files will be moved.",
            text_color="#fbbf24"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        box = ctk.CTkTextbox(window, font=("Consolas", 11))
        box.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        for path in self.files[:2000]:
            category = CATEGORIES.get(path.suffix.lower(), "Other")
            box.insert("end", f"{category + '/':<14}  {path.name}\n")

        if not self.files:
            box.insert("end", "No files found in this folder.")

        box.configure(state="disabled")
        window.protocol("WM_DELETE_WINDOW", window.destroy)

    def batch_rename(self):
        if not self.folder:
            messagebox.showinfo(
                "Choose a folder", "Choose a folder first.",
                parent=self.winfo_toplevel()
            )
            return

        if self.rename_window is not None:
            try:
                if self.rename_window.winfo_exists():
                    self.rename_window.lift()
                    return
            except Exception:
                pass

        dialog = ctk.CTkToplevel(self.winfo_toplevel())
        self.rename_window = dialog
        dialog.title("Batch Rename")
        dialog.geometry("460x250")
        dialog.resizable(False, False)

        ctk.CTkLabel(
            dialog, text="Add a prefix to filenames",
            font=ctk.CTkFont(size=19, weight="bold")
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            dialog, text="Example: project_report.pdf",
            text_color="#94a3b8"
        ).pack()

        entry = ctk.CTkEntry(
            dialog, placeholder_text="Enter prefix, e.g. project_"
        )
        entry.pack(fill="x", padx=24, pady=12)
        entry.focus_set()

        def apply_rename():
            prefix = entry.get().strip()

            if not prefix or any(
                char in prefix for char in '<>:"/\\|?*'
            ):
                messagebox.showwarning(
                    "Invalid prefix",
                    "Enter a valid filename prefix.",
                    parent=dialog
                )
                return

            try:
                current_files = [
                    p for p in self.folder.iterdir() if p.is_file()
                ]
            except OSError as error:
                messagebox.showerror(
                    "Folder error", str(error), parent=dialog
                )
                return

            candidates = [
                p for p in current_files
                if not p.name.startswith(prefix)
            ]

            if not candidates:
                messagebox.showinfo(
                    "No changes", "No files need renaming.",
                    parent=dialog
                )
                return

            sample = "\n".join(
                f"{p.name}  ->  {prefix}{p.name}"
                for p in candidates[:6]
            )

            confirmed = messagebox.askyesno(
                "Confirm Batch Rename",
                f"Rename {len(candidates)} files?\n\n"
                f"{sample}\n\nContinue?",
                parent=dialog
            )
            if not confirmed:
                return

            renamed = 0
            skipped = 0

            for path in candidates:
                target = path.with_name(prefix + path.name)

                if target.exists():
                    skipped += 1
                    continue

                try:
                    path.rename(target)
                    renamed += 1
                except OSError:
                    skipped += 1

            dialog.destroy()
            self.rename_window = None
            self.render()

            messagebox.showinfo(
                "Rename complete",
                f"Successfully renamed: {renamed}\n"
                f"Skipped: {skipped}",
                parent=self.winfo_toplevel()
            )

        ctk.CTkButton(
            dialog, text="Confirm Rename",
            command=apply_rename
        ).pack(pady=(0, 12))

        dialog.protocol(
            "WM_DELETE_WINDOW",
            lambda: self.close_rename_window(dialog)
        )

    def close_rename_window(self, dialog):
        try:
            dialog.destroy()
        finally:
            self.rename_window = None
