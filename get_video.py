#!/usr/bin/env python3
"""Download a video from a URL, with optional resolution selection."""

import subprocess
import sys
import json


def check_yt_dlp():
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def get_formats(url):
    result = subprocess.run(
        ["yt-dlp", "-J", "--no-playlist", url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error fetching video info:\n{result.stderr.strip()}")
        sys.exit(1)

    info = json.loads(result.stdout)
    formats = info.get("formats", [])

    # Collect unique resolutions with video streams
    resolutions = {}
    for f in formats:
        height = f.get("height")
        vcodec = f.get("vcodec", "none")
        if height and vcodec != "none":
            label = f"{height}p"
            if label not in resolutions or (f.get("tbr") or 0) > (resolutions[label].get("tbr") or 0):
                resolutions[label] = f

    return resolutions, info.get("title", "video")


def download(url, format_id=None):
    cmd = ["yt-dlp", "--no-playlist"]
    if format_id:
        cmd += ["-f", f"{format_id}+bestaudio/bestaudio/{format_id}"]
    else:
        cmd += ["-f", "bestvideo+bestaudio/best"]
    cmd += ["--merge-output-format", "mp4", url]

    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    if not check_yt_dlp():
        print("yt-dlp is not installed. Install it with:")
        print("  pip install yt-dlp")
        sys.exit(1)

    url = input("Video URL: ").strip()
    if not url:
        print("No URL provided.")
        sys.exit(1)

    print("Fetching video info...")
    resolutions, title = get_formats(url)

    print(f"\nTitle: {title}")

    if not resolutions:
        print("No resolution options found, downloading best available.")
        success = download(url)
    else:
        sorted_res = sorted(resolutions.keys(), key=lambda r: int(r[:-1]), reverse=True)
        print("\nAvailable resolutions:")
        for i, label in enumerate(sorted_res, 1):
            print(f"  {i}. {label}")

        choice = input("\nResolution (number or e.g. 1080p, or press Enter for best): ").strip()

        selected_format_id = None
        if choice:
            # Accept number or label
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(sorted_res):
                    label = sorted_res[idx]
                    selected_format_id = resolutions[label]["format_id"]
                    print(f"Downloading {label}...")
                else:
                    print("Invalid choice, downloading best available.")
            elif choice in resolutions:
                selected_format_id = resolutions[choice]["format_id"]
                print(f"Downloading {choice}...")
            else:
                print(f"Resolution '{choice}' not found, downloading best available.")
        else:
            print("Downloading best available resolution...")

        success = download(url, selected_format_id)

    if success:
        print("\nDone.")
    else:
        print("\nDownload failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
