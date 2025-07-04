import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter.scrolledtext import ScrolledText
from ttkbootstrap import Style
from ttkbootstrap.widgets import Button, Frame, Progressbar

class AudioJoinerApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Joiner")
        self.geometry("700x500")
        self.style = Style("litera")
        self.files = []

        # === Widgets ===
        self.file_listbox = tk.Listbox(self, selectmode=tk.BROWSE, width=100, height=10)
        self.file_listbox.pack(pady=10, padx=10)
        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind('<<Drop>>', self.drop_files)

        self.button_frame = Frame(self)
        self.button_frame.pack()

        Button(self.button_frame, text="Add Files", command=self.add_files).pack(side="left", padx=5)
        Button(self.button_frame, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=5)
        Button(self.button_frame, text="Clear All", command=self.clear_all).pack(side="left", padx=5)
        Button(self.button_frame, text="Start Join", bootstyle="success", command=self.start_joining).pack(side="left", padx=5)

        self.progress = Progressbar(self, orient='horizontal', mode='determinate')
        self.progress.pack(fill='x', padx=10, pady=10)

        self.log = ScrolledText(self, height=12)
        self.log.pack(fill='both', expand=True, padx=10, pady=5)

    def drop_files(self, event):
        dropped = self.tk.splitlist(event.data)
        for file in dropped:
            if file.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a')) and file not in self.files:
                self.files.append(file)
                self.file_listbox.insert(tk.END, file)
                self.log_debug(f"Dropped: {file}")

    def add_files(self):
        new_files = filedialog.askopenfilenames(filetypes=[("Audio files", "*.mp3 *.wav *.flac *.aac *.ogg *.m4a")])
        for file in new_files:
            if file not in self.files:
                self.files.append(file)
                self.file_listbox.insert(tk.END, file)
                self.log_debug(f"Added: {file}")

    def remove_selected(self):
        selection = self.file_listbox.curselection()
        if selection:
            idx = selection[0]
            removed = self.files.pop(idx)
            self.file_listbox.delete(idx)
            self.log_debug(f"Removed: {removed}")

    def clear_all(self):
        self.files.clear()
        self.file_listbox.delete(0, tk.END)
        self.log_debug("Cleared all files.")

    def start_joining(self):
        if len(self.files) < 2:
            messagebox.showerror("Error", "Please select at least two audio files.")
            return
        threading.Thread(target=self.join_files, daemon=True).start()

    def join_files(self):
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.files) + 2

        try:
            # Detect codec and bitrate from first file
            probe_cmd = [
                "ffprobe", "-v", "error", "-select_streams", "a:0",
                "-show_entries", "stream=codec_name,bit_rate",
                "-of", "default=noprint_wrappers=1:nokey=1",
                self.files[0]
            ]
            result = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            info = result.stdout.strip().splitlines()
            codec = info[0] if info else "copy"
            bitrate = info[1] if len(info) > 1 else None
            self.progress.step()
            self.update_idletasks()

            self.log_debug(f"Detected codec: {codec}, bitrate: {bitrate}")

            with open("input.txt", "w", encoding="utf-8") as f:
                for file in self.files:
                    safe_path = file.replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")
                    self.progress.step()
                    self.update_idletasks()

            output_ext = os.path.splitext(self.files[0])[1]
            output_name = f"joined_output{output_ext}"

            cmd = [
                "ffmpeg", "-f", "concat", "-safe", "0",
                "-i", "input.txt", "-c", codec, output_name
            ]
            if bitrate:
                cmd += ["-b:a", bitrate]

            self.log_debug(f"Running: {' '.join(cmd)}")
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            self.progress["value"] = self.progress["maximum"]
            self.log_debug(f"✅ Audio joined into: {output_name}")

        except Exception as e:
            self.log_debug(f"❌ Error: {e}")

    def log_debug(self, msg):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

if __name__ == "__main__":
    app = AudioJoinerApp()
    app.mainloop()
