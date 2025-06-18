#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
from pathlib import Path
from PIL import Image
import pillow_heif # Enables HEIC/AVIF support in Pillow (for iPhone images, etc.)
pillow_heif.register_heif_opener() # Register HEIC/AVIF support so Pillow can open iPhone images (.heic)

def scrub_file(file_path):
    try:
        subprocess.run([
            "exiftool",
            "-all=",
            "-thumbnailimage=",
            "-overwrite_original",
            str(file_path)
        ], check=True)
        print(f"[+] Scrubbed: {file_path}")
    except subprocess.CalledProcessError:
        print(f"[!] Failed to scrub: {file_path}")

def reset_timestamps(file_path):
    Path(file_path).touch()
    print(f"[+] Reset timestamps: {file_path}")

def is_image(file_path):
    return file_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".tiff", ".heic"]

def collect_files(paths):
    collected = []
    for p in paths:
        path = Path(p)
        if path.is_file() and is_image(path):
            collected.append(path)
        elif path.is_dir():
            for f in path.rglob("*"):
                if f.is_file() and is_image(f):
                    collected.append(f)
    return collected

def convert_to_jpeg(file_path, output_path):
    try:
        with Image.open(file_path) as img:
            rgb = img.convert("RGB")  # Ensures compatibility for JPEG
            rgb.save(output_path, format="JPEG", quality=95)
        print(f"[+] Converted to JPEG: {output_path}")
    except Exception as e:
        print(f"[!] Failed to convert {file_path} to JPEG: {e}")

def rename_file(file_path, index, dest_dir, to_jpeg=False):
    ext = ".jpg" if to_jpeg else file_path.suffix.lower()
    new_name = f"photo_{index:03d}{ext}"
    new_path = dest_dir / new_name
    return new_path

def main():
    parser = argparse.ArgumentParser(description="Scrub EXIF metadata, optionally convert to JPEG, and rename images.")
    parser.add_argument("paths", nargs="+", help="Files or directories to process")
    parser.add_argument("-r", "--reset-time", action="store_true", help="Reset file timestamps")
    parser.add_argument("-d", "--dest", help="Destination directory (default: same as original)")
    parser.add_argument("-j", "--to-jpeg", action="store_true", help="Convert all images to JPEG format")
    args = parser.parse_args()

    files = collect_files(args.paths)
    if not files:
        print("[-] No image files found.")
        sys.exit(1)

    dest_dir = Path(args.dest).resolve() if args.dest else None
    if dest_dir and not dest_dir.exists():
        dest_dir.mkdir(parents=True)

    for idx, f in enumerate(files, start=1):
        scrub_file(f)

        if args.reset_time:
            reset_timestamps(f)

        output_dir = dest_dir if dest_dir else f.parent
        new_path = rename_file(f, idx, output_dir, to_jpeg=args.to_jpeg)

        if args.to_jpeg:
            convert_to_jpeg(f, new_path)
        else:
            f.rename(new_path)
            print(f"[+] Renamed to: {new_path}")

if __name__ == "__main__":
    main()

