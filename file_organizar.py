"""
file_organizer_gui_advanced.py
Advanced Tkinter File Organizer with:
 - Duplicate handling
 - Background threading
 - Neon gradient progress bar with animation
 - Dark hacker terminal with animated cursor
 - Modern gradient cards and hover buttons
"""

import os
import shutil
import threading
import queue
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# ---------------- Configuration ----------------
FILE_TYPES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".pptx", ".ppt", ".xlsx", ".xls", ".odt", ".rtf"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".wmv"],
    "Music": [".mp3", ".wav", ".aac", ".flac", ".ogg"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
}
OTHER_FOLDER_NAME = "Others"

COLORS = {
    "dark": {
        "bg_primary": "#0a0e13",
        "bg_card": "#1c2128",
        "accent_primary": "#00ff88",
        "accent_secondary": "#00d4ff",
        "accent_warning": "#ffaa00",
        "accent_danger": "#ff4444",
        "text_primary": "#00ff88",
        "text_secondary": "#8b949e",
        "terminal_bg": "#0a0a0a",
        "terminal_fg": "#00ff88",
        "button_hover": "#00d4ff",
        "progress_gradient": ["#00ff88","#00d4ff","#00ff88","#00d4ff"]
    }
}

# ---------------- Utilities ----------------
def get_unique_name(dest_dir, filename):
    base, ext = os.path.splitext(filename)
    candidate = filename
    counter = 1
    while os.path.exists(os.path.join(dest_dir, candidate)):
        candidate = f"{base} ({counter}){ext}"
        counter += 1
    return candidate

def categorize_file(filename):
    lower = filename.lower()
    for cat, exts in FILE_TYPES.items():
        if lower.endswith(tuple(exts)):
            return cat
    return None

# ---------------- Worker ----------------
class OrganizerWorker(threading.Thread):
    def __init__(self, source, dest, queue_out):
        super().__init__()
        self.source = source
        self.dest = dest
        self.queue_out = queue_out
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        try:
            files = [f for f in os.listdir(self.source) if os.path.isfile(os.path.join(self.source, f))]
        except Exception as e:
            self.queue_out.put(("error", f"Failed to list source folder: {e}"))
            return

        total = len(files)
        moved_count = 0
        self.queue_out.put(("start", total))

        for cat in FILE_TYPES.keys():
            os.makedirs(os.path.join(self.dest, cat), exist_ok=True)
        os.makedirs(os.path.join(self.dest, OTHER_FOLDER_NAME), exist_ok=True)

        for idx, filename in enumerate(files, start=1):
            if self.stopped():
                self.queue_out.put(("log", f"[SYS] Operation cancelled by user."))
                break
            src_path = os.path.join(self.source, filename)
            try:
                if not os.path.isfile(src_path):
                    self.queue_out.put(("log", f"[SYS] Skipping (not a file): {filename}"))
                    self.queue_out.put(("progress", idx))
                    continue

                category = categorize_file(filename) or OTHER_FOLDER_NAME
                dest_folder = os.path.join(self.dest, category)
                os.makedirs(dest_folder, exist_ok=True)

                unique_name = get_unique_name(dest_folder, filename)
                dest_path = os.path.join(dest_folder, unique_name)
                shutil.move(src_path, dest_path)
                moved_count += 1
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                self.queue_out.put(("log", f"[SYS] [{timestamp}] Moved: {filename} → {category}/{unique_name}"))
            except Exception as e:
                self.queue_out.put(("log", f"[SYS] ERROR moving {filename}: {e}"))

            self.queue_out.put(("progress", idx))

        self.queue_out.put(("done", moved_count))

# ---------------- GUI ----------------
class FileOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.queue = queue.Queue()
        self.worker = None

        self.source_var = tk.StringVar()
        self.dest_var = tk.StringVar()

        self._setup_window()
        self._build_ui()
        self.gradient_index = 0
        self._animate_terminal_cursor()
        self._animate_progress_gradient()
        self.root.after(100, self._process_queue)

    def _setup_window(self):
        self.root.title("File Organizer")
        self.root.geometry("950x700")
        self.root.configure(bg=COLORS["dark"]["bg_primary"])

    def _build_ui(self):
        main_frame = tk.Frame(self.root, bg=COLORS["dark"]["bg_primary"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        header = tk.Label(main_frame, text="💻 FILE ORGANIZER PRO v2.0", font=("Consolas", 18, "bold"),
                          fg=COLORS["dark"]["accent_primary"], bg=COLORS["dark"]["bg_primary"])
        header.pack(pady=(0,10))

        # Folder selection card
        card = tk.Frame(main_frame, bg=COLORS["dark"]["bg_card"], bd=2, relief="raised")
        card.pack(fill="x", padx=10, pady=10)

        tk.Label(card, text="Source Folder:", fg=COLORS["dark"]["text_primary"], bg=COLORS["dark"]["bg_card"], font=("Consolas",11)).pack(anchor="w", padx=5, pady=(5,0))
        src_frame = tk.Frame(card, bg=COLORS["dark"]["bg_card"])
        src_frame.pack(fill="x", padx=5, pady=5)
        self.source_entry = tk.Entry(src_frame, textvariable=self.source_var, bg="#111", fg=COLORS["dark"]["text_primary"], insertbackground=COLORS["dark"]["text_primary"], font=("Consolas",11))
        self.source_entry.pack(side="left", fill="x", expand=True)
        self._styled_button(src_frame, "Browse", self._browse_source).pack(side="left", padx=5)

        tk.Label(card, text="Destination Folder:", fg=COLORS["dark"]["text_primary"], bg=COLORS["dark"]["bg_card"], font=("Consolas",11)).pack(anchor="w", padx=5)
        dst_frame = tk.Frame(card, bg=COLORS["dark"]["bg_card"])
        dst_frame.pack(fill="x", padx=5, pady=5)
        self.dest_entry = tk.Entry(dst_frame, textvariable=self.dest_var, bg="#111", fg=COLORS["dark"]["text_primary"], insertbackground=COLORS["dark"]["text_primary"], font=("Consolas",11))
        self.dest_entry.pack(side="left", fill="x", expand=True)
        self._styled_button(dst_frame, "Browse", self._browse_dest).pack(side="left", padx=5)

        # Buttons
        btn_frame = tk.Frame(main_frame, bg=COLORS["dark"]["bg_primary"])
        btn_frame.pack(fill="x", pady=10)
        self.organize_btn = self._styled_button(btn_frame, "🚀 Start Organization", self._on_organize, width=20)
        self.organize_btn.pack(side="left", padx=5)
        self.cancel_btn = self._styled_button(btn_frame, "⏹️ Cancel", self._on_cancel, width=15, bg=COLORS["dark"]["accent_danger"])
        self.cancel_btn.pack(side="left", padx=5)
        self.cancel_btn.config(state="disabled")

        # Canvas-based gradient progress bar
        self.progress_canvas = tk.Canvas(main_frame, height=25, bg="#111", bd=0, highlightthickness=0)
        self.progress_canvas.pack(fill="x", pady=10)
        self.progress_rect = self.progress_canvas.create_rectangle(0,0,0,25, fill=COLORS["dark"]["progress_gradient"][0], width=0)
        self.progress_value = 0
        self.progress_max = 100

        # Terminal
        terminal_frame = tk.Frame(main_frame, bg=COLORS["dark"]["terminal_bg"], bd=2, relief="sunken")
        terminal_frame.pack(fill="both", expand=True, pady=5)
        self.log_area = scrolledtext.ScrolledText(terminal_frame, wrap="word", bg=COLORS["dark"]["terminal_bg"],
                                                  fg=COLORS["dark"]["terminal_fg"], insertbackground=COLORS["dark"]["terminal_fg"],
                                                  font=("Consolas", 11))
        self.log_area.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_area.configure(state="disabled")
        self._log("=== FILE ORGANIZER PRO v2.0 ===")
        self._log("Terminal ready...")

    # ---------- Styled Button ----------
    def _styled_button(self, parent, text, command, width=None, bg=None):
        btn_bg = bg or COLORS["dark"]["accent_primary"]
        btn = tk.Button(parent, text=text, command=command, bg=btn_bg, fg="#000",
                        font=("Consolas", 11, "bold"), activebackground=COLORS["dark"]["button_hover"])
        if width:
            btn.config(width=width)
        btn.bind("<Enter>", lambda e: btn.config(bg=COLORS["dark"]["button_hover"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=btn_bg))
        return btn

    # ---------- Terminal ----------
    def _log(self, msg):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", msg + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    # ---------- Gradient Progress Animation ----------
    def _animate_progress_gradient(self):
        gradient = COLORS["dark"]["progress_gradient"]
        if self.progress_value > 0:
            target_width = (self.progress_value/self.progress_max)*self.progress_canvas.winfo_width()
            current_width = self.progress_canvas.coords(self.progress_rect)[2]
            new_width = current_width + (target_width - current_width) * 0.2
            self.progress_canvas.coords(self.progress_rect, 0, 0, new_width, 25)
            color = gradient[self.gradient_index % len(gradient)]
            self.progress_canvas.itemconfig(self.progress_rect, fill=color)
            self.gradient_index += 1
        self.root.after(80, self._animate_progress_gradient)

    # ---------- Terminal cursor ----------
    def _animate_terminal_cursor(self):
        self.log_area.configure(state="normal")
        content = self.log_area.get("1.0", "end-1c")
        if content.endswith("_"):
            self.log_area.delete("end-2c")
        else:
            self.log_area.insert("end", "_")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")
        self.root.after(500, self._animate_terminal_cursor)

    # ---------- Folder Browsers ----------
    def _browse_source(self):
        folder = filedialog.askdirectory(title="Select Source Folder")
        if folder:
            self.source_var.set(folder)
            self._log(f"[SYS] Source folder: {folder}")

    def _browse_dest(self):
        folder = filedialog.askdirectory(title="Select Destination Folder")
        if folder:
            self.dest_var.set(folder)
            self._log(f"[SYS] Destination folder: {folder}")

    # ---------- Organize ----------
    def _on_organize(self):
        src = self.source_var.get()
        dst = self.dest_var.get()
        if not src or not dst:
            messagebox.showerror("Error","Please select source and destination folders")
            return
        self.organize_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress_value = 0
        self.progress_max = len([f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f))])
        self.worker = OrganizerWorker(src, dst, self.queue)
        self.worker.start()
        self._log("[SYS] Organization started...")

    def _on_cancel(self):
        if self.worker and self.worker.is_alive():
            self.worker.stop()
            self._log("[SYS] Cancel requested...")
        else:
            self._log("[SYS] No active operation to cancel.")

    # ---------- Queue ----------
    def _process_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                kind,payload = item
                if kind=="progress":
                    self.progress_value = payload
                elif kind=="log":
                    self._log(payload)
                elif kind=="done":
                    self.progress_value = self.progress_max
                    self._log(f"[SYS] Completed! {payload} files organized.")
                    messagebox.showinfo("Success", f"{payload} files organized!")
                    self.organize_btn.config(state="normal")
                    self.cancel_btn.config(state="disabled")
        except queue.Empty:
            pass
        self.root.after(100,self._process_queue)

# ---------------- Entry ----------------
if __name__=="__main__":
    root = tk.Tk()
    app = FileOrganizerGUI(root)
    root.mainloop()
