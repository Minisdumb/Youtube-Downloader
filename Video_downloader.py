import tkinter
import threading
import json
import os
import customtkinter
from yt_dlp import YoutubeDL
import zipfile
import urllib.request
import shutil
import sys


FFMPEG_DIR = os.path.join(
    os.path.dirname(sys.executable if getattr(sys, "frozen", False) else __file__),
    "ffmpeg"
)


def install_ffmpeg():

    ffmpeg_exe = os.path.join(FFMPEG_DIR, "bin", "ffmpeg.exe")

    if os.path.exists(ffmpeg_exe):
        return os.path.join(FFMPEG_DIR,"bin")


    print("Installing FFmpeg... Please wait, This may take a minute.")

    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

    zip_path = "ffmpeg.zip"

    urllib.request.urlretrieve(url, zip_path)


    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall("temp_ffmpeg")


    # Find the actual folder containing bin/ffmpeg.exe
    ffmpeg_root = None

    for root, dirs, files in os.walk("temp_ffmpeg"):
        if "ffmpeg.exe" in files:
            ffmpeg_root = root.replace("\\bin", "")
            break

    if ffmpeg_root is None:
        raise Exception("Could not find ffmpeg.exe after extraction")


    # Create final FFmpeg directory
    os.makedirs(FFMPEG_DIR, exist_ok=True)


    # Copy the whole FFmpeg folder contents
    for item in os.listdir(ffmpeg_root):
        source = os.path.join(ffmpeg_root, item)
        destination = os.path.join(FFMPEG_DIR, item)

        if os.path.isdir(source):
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)

    os.remove(zip_path)
    shutil.rmtree("temp_ffmpeg")

    print(FFMPEG_DIR)
    return os.path.join(FFMPEG_DIR,"bin")

# =========================
# LOAD CONFIG
# =========================

FFMPEG_PATH = install_ffmpeg()

# =========================
# GUI SETUP
# =========================

customtkinter.set_appearance_mode("system")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
app.geometry(f"{int(app.winfo_screenwidth() / 3)}x{int(app.winfo_screenheight() / 3)}")
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
                print(FFMPEG_PATH + " is the path")
                ydl_opts["ffmpeg_location"] = FFMPEG_PATH

            with YoutubeDL(ydl_opts) as ydl:
                ydl.params["ffmpeg_location"] = FFMPEG_PATH
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
download_btn.pack()

# =========================
# RUN APP
# =========================

app.mainloop()