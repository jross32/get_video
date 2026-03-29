#!/usr/bin/env python3
"""Download videos from one or more URLs, with optional resolution selection."""

import subprocess
import sys
import json
import os
from urllib.parse import urlparse


def check_yt_dlp():
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def get_formats(url, cookies_browser=None):
    cmd = ["yt-dlp", "-J", "--no-playlist"]
    if cookies_browser:
        cmd += ["--cookies-from-browser", cookies_browser]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Error fetching video info:\n  {result.stderr.strip()}")
        return None, None

    info = json.loads(result.stdout)
    formats = info.get("formats", [])

    resolutions = {}
    for f in formats:
        height = f.get("height")
        vcodec = f.get("vcodec", "none")
        if height and vcodec != "none":
            label = f"{height}p"
            if label not in resolutions or (f.get("tbr") or 0) > (resolutions[label].get("tbr") or 0):
                resolutions[label] = f

    return resolutions, info.get("title", "video")


def site_name(url):
    host = urlparse(url).hostname or ""
    # Strip www. and take the first part, e.g. www.youtube.com -> youtube
    host = host.removeprefix("www.")
    return host.split(".")[0] or "unknown"


def output_dir(url):
    folder = os.path.join("saved_videos", site_name(url))
    os.makedirs(folder, exist_ok=True)
    return folder


def download(url, format_id=None, cookies_browser=None):
    folder = output_dir(url)
    cmd = ["yt-dlp", "--no-playlist"]
    if format_id:
        cmd += ["-f", f"{format_id}+bestaudio/bestaudio/{format_id}"]
    else:
        cmd += ["-f", "bestvideo+bestaudio/best"]
    if cookies_browser:
        cmd += ["--cookies-from-browser", cookies_browser]
    cmd += [
        "--merge-output-format", "mp4",
        "-o", os.path.join(folder, "%(title)s.%(ext)s"),
        "--trim-filenames", "100",
        "--windows-filenames",
        url,
    ]

    result = subprocess.run(cmd)
    return result.returncode == 0


def prompt_urls():
    print("Enter video URLs one per line.")
    print("Press Enter on an empty line when done.\n")
    urls = []
    while True:
        line = input(f"  URL {len(urls) + 1}: ").strip()
        if not line:
            if not urls:
                print("No URLs entered.")
                sys.exit(1)
            break
        urls.append(line)
    return urls


def handle_video(index, total, url, cookies_browser=None):
    print(f"\n[{index}/{total}] Fetching info for: {url}")
    print(f"  Saving to: saved_videos/{site_name(url)}/")
    resolutions, title = get_formats(url, cookies_browser)

    if title is None:
        print(f"  Skipping due to error.")
        return False

    print(f"  Title: {title}")

    selected_format_id = None

    if resolutions:
        sorted_res = sorted(resolutions.keys(), key=lambda r: int(r[:-1]), reverse=True)
        print("  Available resolutions: " + ", ".join(sorted_res))
        choice = input("  Resolution (number or e.g. 1080p, or Enter for best): ").strip()

        if choice:
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(sorted_res):
                    label = sorted_res[idx]
                    selected_format_id = resolutions[label]["format_id"]
                    print(f"  Downloading {label}...")
                else:
                    print("  Invalid choice, downloading best available.")
            elif choice in resolutions:
                selected_format_id = resolutions[choice]["format_id"]
                print(f"  Downloading {choice}...")
            else:
                print(f"  Resolution '{choice}' not found, downloading best available.")
        else:
            print("  Downloading best available resolution...")
    else:
        print("  No resolution options found, downloading best available.")

    return download(url, selected_format_id, cookies_browser)


def main():
    if not check_yt_dlp():
        print("yt-dlp is not installed. Install it with:")
        print("  pip install yt-dlp")
        sys.exit(1)

    cookies_browser = "chrome"

    urls = prompt_urls()
    total = len(urls)
    results = []

    for i, url in enumerate(urls, 1):
        success = handle_video(i, total, url, cookies_browser)
        results.append((url, success))

    print("\n--- Summary ---")
    for url, success in results:
        status = "OK" if success else "FAILED"
        print(f"  [{status}] {url}")


if __name__ == "__main__":
    main()
