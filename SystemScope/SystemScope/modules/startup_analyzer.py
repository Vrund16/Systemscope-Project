"""Read-only Windows startup entry viewer; never disables or changes entries."""
import os
import sys
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox

BG="#0b1020"; PANEL="#121a2d"; MUTED="#9aa8bf"; WHITE="#f4f7ff"; BLUE="#7c9cff"
class StartupAnalyzer(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG)
        ctk.CTkLabel(self,text="Startup & Background Apps",font=ctk.CTkFont(size=28,weight="bold"),text_color=WHITE).pack(anchor="w",padx=24,pady=(22,4))
        ctk.CTkLabel(self,text="Read-only view of common Windows startup locations. Nothing is disabled or changed.",text_color=MUTED).pack(anchor="w",padx=26,pady=(0,16))
        bar=ctk.CTkFrame(self,fg_color="transparent"); bar.pack(fill="x",padx=24)
        ctk.CTkButton(bar,text="Scan startup locations",command=self.scan).pack(side="left")
        self.status=ctk.CTkLabel(bar,text="Ready to scan",text_color=MUTED); self.status.pack(side="left",padx=12)
        self.output=ctk.CTkTextbox(self,fg_color=PANEL,text_color="#dce6fb",font=ctk.CTkFont(size=12),corner_radius=14)
        self.output.pack(fill="both",expand=True,padx=24,pady=16)
        self.output.insert("end","Scan to view shortcut files and common Run registry entries.\n\nThis tool does not estimate impact or automatically disable anything. Review unknown entries carefully before changing Windows settings.")
    def scan(self):
        if sys.platform != "win32":
            messagebox.showinfo("Windows only","Startup registry scanning is available on Windows.",parent=self.winfo_toplevel()); return
        items=[]; errors=[]
        folders=[Path(os.environ.get("APPDATA",""))/r"Microsoft\Windows\Start Menu\Programs\Startup",Path(os.environ.get("PROGRAMDATA",r"C:\ProgramData"))/r"Microsoft\Windows\Start Menu\Programs\Startup"]
        for folder in folders:
            if folder.exists():
                try:
                    for p in folder.iterdir(): items.append(("Startup folder",p.name,str(p)))
                except OSError as e: errors.append(f"{folder}: {e}")
        try:
            import winreg
            locations=[(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run","HKCU Run"),(winreg.HKEY_LOCAL_MACHINE,r"Software\Microsoft\Windows\CurrentVersion\Run","HKLM Run"),(winreg.HKEY_LOCAL_MACHINE,r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run","HKLM Run (32-bit)")]
            for hive,key,label in locations:
                try:
                    with winreg.OpenKey(hive,key) as handle:
                        i=0
                        while True:
                            try:
                                name,value,_=winreg.EnumValue(handle,i); items.append((label,name,str(value))); i+=1
                            except OSError: break
                except FileNotFoundError: pass
                except OSError as e: errors.append(f"{label}: {e}")
        except Exception as e: errors.append(str(e))
        lines=["STARTUP INVENTORY", "="*78, f"Entries found: {len(items)}", "", "Entries are listed for review only; this is not a malware verdict.", ""]
        lines += [f"[{kind}] {name}\n    {value}\n" for kind,name,value in sorted(items,key=lambda x:(x[0].lower(),x[1].lower()))]
        if not items: lines.append("No entries found in the scanned locations.")
        if errors: lines += ["", "ACCESS NOTES", *errors]
        self.output.delete("1.0","end"); self.output.insert("end","\n".join(lines)); self.status.configure(text=f"Scan complete · {len(items)} entries")
