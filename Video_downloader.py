import tkinter
import threading
import json
import os
import customtkinter
from yt_dlp import YoutubeDL

# =========================
# LOAD CONFIG
# =========================

CONFIG_FILE = "config.json"

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = {}

FFMPEG_PATH = config.get("ffmpeg_path")
NODE_PATH = config.get("node_path")

# =========================
# GUI SETUP
# =========================

customtkinter.set_appearance_mode("system")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
app.geometry(f"{int(app.winfo_screenwidth() / 2)}x{int(app.winfo_screenheight() / 2)}")
app.title("YT Downloader")
app.resizable(False, False)

url = tkinter.StringVar()

title = customtkinter.CTkLabel(app, text="ENTER LINK:")
title.pack(pady=20)

link = customtkinter.CTkEntry(
    app,
    width=360,
    height=40,
    placeholder_text="PASTE LINK HERE",
    textvariable=url
)
link.pack()

progress_label = customtkinter.CTkLabel(app, text="0%")
progress_label.pack(pady=10)

pProgress = customtkinter.CTkProgressBar(app, width=400)
pProgress.pack()
pProgress.set(0)

finished = customtkinter.CTkLabel(app, text="")
finished.pack(pady=20)

# =========================
# SAFE UI UPDATE WRAPPER
# =========================

def ui_update(func):
    app.after(0, func)

# =========================
# PROGRESS HOOK
# =========================

def process_hook(d):
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)

        percent = downloaded / total if total else 0

        ui_update(lambda: progress_label.configure(text=f"{percent*100:.1f}%"))
        ui_update(lambda: pProgress.set(percent))

    elif d['status'] == 'finished':
        ui_update(lambda: pProgress.set(1))
        ui_update(lambda: progress_label.configure(text="DONE"))

# =========================
# DOWNLOAD FUNCTION
# =========================

def download_vid():
    def run():
        try:
            ytlink = link.get()

            ydl_opts = {
                "progress_hooks": [process_hook],
                "outtmpl": "%(title)s.%(ext)s",
                "format": "bv*+ba/b",
                "quiet": True,
                "no_warnings": True,
                "merge_output_format": "mp4",
            }

            # FFmpeg config (required for merging)
            if FFMPEG_PATH:
                ydl_opts["ffmpeg_location"] = FFMPEG_PATH

            # Node.js runtime (optional, for new yt-dlp YouTube JS extraction)
            if NODE_PATH:
                ydl_opts["js_runtimes"] = {
                    "node": NODE_PATH
                }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.params["ffmpeg_location"] = r"C:/ffmpeg/bin"
                info = ydl.extract_info(ytlink, download=True)

            ui_update(lambda: finished.configure(
                text=f"DOWNLOAD DONE: {info.get('title', 'Unknown')}",
                text_color="green"
            ))

        except Exception as e:
            ui_update(lambda: finished.configure(
                text=f"ERROR: {e}",
                text_color="red"
            ))

    threading.Thread(target=run, daemon=True).start()

# =========================
# BUTTON
# =========================

download_btn = customtkinter.CTkButton(
    app,
    text="DOWNLOAD",
    command=download_vid
)
download_btn.pack(pady=20)

# =========================
# RUN APP
# =========================

app.mainloop()