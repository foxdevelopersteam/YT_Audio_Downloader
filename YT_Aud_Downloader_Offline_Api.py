"""
YouTube downloader using yt-dlp (works with or without ffmpeg).

Install:  pip install yt-dlp
Optional (for 1080p on Android, try it): pip install imageio-ffmpeg
Usage:    python yt_downloader.py
"""

import os
import shutil

import yt_dlp

QUALITIES = {"1": 360, "2": 480, "3": 720, "4": 1080}


def find_ffmpeg():
    """Return path to ffmpeg if available (system or imageio-ffmpeg), else None."""
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass
    return None


FFMPEG = find_ffmpeg()


def default_out_dir() -> str:
    android = "/storage/emulated/0/_15_OFFLINE_MUSIC_LIBRARY_"
    try:
        os.makedirs(android, exist_ok=True)
        return android
    except OSError:
        return "downloads"


def build_attempts(audio_only: bool, height: int):
    """List of (format, extractor_args) to try in order until one works."""
    app_clients = {"youtube": {"player_client": ["android", "ios"]}}

    if audio_only:
        return [("bestaudio[ext=m4a]/bestaudio", None)]

    if FFMPEG:
        merged = (f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]"
                  f"/bestvideo[height<={height}]+bestaudio/best[height<={height}]")
        return [(merged, None), (merged, app_clients), ("best", None)]

    single = f"best[height<={height}][ext=mp4]/best[height<={height}]"
    return [(single, None), (single, app_clients), ("18", app_clients), ("best", None)]


def download(url, audio_only=False, height=1080, playlist=False, out_dir="downloads"):
    if playlist:
        template = f"{out_dir}/%(playlist_title)s/%(playlist_index)02d - %(title)s.%(ext)s"
    else:
        template = f"{out_dir}/%(title)s.%(ext)s"

    last_error = None
    for fmt, extractor_args in build_attempts(audio_only, height):
        options = {
            "outtmpl": template,
            "noplaylist": not playlist,
            "ignoreerrors": playlist,
            "format": fmt,
        }
        if FFMPEG:
            options["ffmpeg_location"] = FFMPEG
            if not audio_only:
                options["merge_output_format"] = "mp4"
            else:
                options["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
                options["format"] = "bestaudio/best"
        if extractor_args:
            options["extractor_args"] = extractor_args

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
            return
        except Exception as e:
            last_error = e
            print(f"\nAttempt with format '{fmt}' failed, trying next option...\n")

    raise last_error


def main() -> None:
    if FFMPEG:
        print("ffmpeg found -> full quality mode.\n")
    else:
        print("ffmpeg not found -> single-file mode (max ~720p, audio as m4a).\n")

    url = input("Paste video or playlist URL: ").strip()

    playlist = False
    if "list=" in url:
        playlist = input("Download the whole playlist? [y/n]: ").strip().lower() == "y"

    choice = input("Download (v)ideo or (a)udio only? [v/a]: ").strip().lower()

    height = 1080
    if choice != "a":
        print("Quality: 1) 360p  2) 480p  3) 720p  4) 1080p (default)")
        height = QUALITIES.get(input("Choose [1-4]: ").strip(), 1080)

    out_dir = default_out_dir()
    try:
        download(url, audio_only=(choice == "a"), height=height,
                 playlist=playlist, out_dir=out_dir)
        print(f"Done! Saved in: {out_dir}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
