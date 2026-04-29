#!/usr/bin/env python3
"""Twitter/X thread comment crawler for glowing-giggle.

This script loads a CSV of tweet URLs and crawls thread replies for each URL.
"""

import os
import shlex
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

from dotenv import load_dotenv
import pandas as pd

# Load .env from script directory
load_dotenv(Path(__file__).resolve().parent / ".env")

TWITTER_AUTH_TOKEN = os.environ.get("TWITTER_AUTH_TOKEN")
INPUT_CSV_PATH = os.environ.get("INPUT_CSV_PATH")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "thread-comments")
GDRIVE_DIR = os.environ.get("GDRIVE_DIR", "")
TWEET_LIMIT = int(os.environ.get("TWEET_LIMIT", "15000"))
MAX_THREADS = int(os.environ.get("MAX_THREADS", "0"))


def run_command(command: str) -> tuple[int, str]:
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output = result.stdout + result.stderr
    if result.returncode != 0:
        print(output)
    return result.returncode, output


def build_filename(prefix: str, part: int) -> str:
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    return f"{prefix}_{timestamp}_part{part}.csv"


def find_input_path() -> str:
    if INPUT_CSV_PATH:
        return INPUT_CSV_PATH
    raise FileNotFoundError("INPUT_CSV_PATH is not set.")


def load_sorted_urls(csv_path: str) -> List[str]:
    df = pd.read_csv(csv_path, dtype=str)
    if df.empty:
        return []

    if "retweet_count" in df.columns:
        df["retweet_count"] = pd.to_numeric(df["retweet_count"], errors="coerce").fillna(0)
        df_sorted = df.sort_values(by="retweet_count", ascending=False)
        print("Sorted by retweet_count descending.")
    elif "created_at" in df.columns:
        df_sorted = df.sort_values(by="created_at", ascending=False)
        print("retweet_count not found; sorted by created_at descending.")
    else:
        df_sorted = df
        print("Neither retweet_count nor created_at found; using original order.")

    if "tweet_url" not in df_sorted.columns:
        raise KeyError("Column 'tweet_url' not found in input CSV.")

    urls = [url for url in df_sorted["tweet_url"].dropna().astype(str).unique() if url.strip()]
    print(f"Found {len(urls)} unique tweet URLs.")
    return urls


def copy_to_gdrive(src: Path, dest_dir: str) -> Path:
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = Path(dest_dir) / src.name
    df = pd.read_csv(src, dtype=str)
    df.to_csv(dest_path, index=False)
    return dest_path


def main() -> int:
    if not TWITTER_AUTH_TOKEN:
        print("Error: TWITTER_AUTH_TOKEN environment variable is required.")
        return 1

    try:
        input_path = find_input_path()
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1

    if not os.path.exists(input_path):
        print(f"Error: Input CSV not found at {input_path}")
        return 1

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    temp_dir = Path(OUTPUT_DIR) / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        tweet_urls = load_sorted_urls(input_path)
    except Exception as exc:
        print(f"Error reading input CSV: {exc}")
        return 1

    if MAX_THREADS > 0:
        tweet_urls = tweet_urls[:MAX_THREADS]
        print(f"Limiting crawl to first {len(tweet_urls)} thread URLs.")

    if not tweet_urls:
        print("No tweet URLs found to crawl.")
        return 0

    thread_frames: List[pd.DataFrame] = []
    for idx, url in enumerate(tweet_urls, start=1):
        print(f"Crawling thread {idx}/{len(tweet_urls)}: {url}")
        output_file = temp_dir / build_filename("thread_comments", idx)

        command = (
            f'npx --yes tweet-harvest@latest -o {shlex.quote(str(output_file))} '
            f'-l {TWEET_LIMIT} --token {shlex.quote(TWITTER_AUTH_TOKEN)} --thread {shlex.quote(url)}'
        )

        exit_code, output = run_command(command)
        if exit_code != 0:
            if "libatk-1.0.so.0" in output or "cannot open shared object file" in output:
                print(
                    "Error: Chromium dependencies are missing for tweet-harvest. "
                    "Install system packages like libatk1.0-0, libatk-bridge2.0-0, libcups2, libxss1, libx11-xcb1, libdrm2, libgtk-3-0, libnss3."
                )
            print(f"Warning: tweet-harvest exited with code {exit_code} for URL {url}")
            continue

        if not output_file.exists() or output_file.stat().st_size == 0:
            print(f"Warning: no output created for thread {url}")
            continue

        try:
            df_thread = pd.read_csv(output_file, dtype=str)
        except Exception as exc:
            print(f"Warning: failed to read thread CSV {output_file}: {exc}")
            continue

        if df_thread.empty:
            print(f"Warning: thread CSV is empty for {url}")
            continue

        print(f"Crawled {len(df_thread)} comments for thread {idx}.")
        thread_frames.append(df_thread)

    if not thread_frames:
        print("No thread comments were collected.")
        return 0

    combined = pd.concat(thread_frames, ignore_index=True)
    final_filename = f"thread_comments_combined_sorted_{datetime.now().strftime('%d%m%Y_%H%M%S')}.csv"
    final_path = Path(OUTPUT_DIR) / final_filename
    combined.to_csv(final_path, index=False)
    print(f"Saved combined comments CSV: {final_path}")

    if GDRIVE_DIR:
        try:
            gdrive_path = copy_to_gdrive(final_path, GDRIVE_DIR)
            print(f"Copied combined CSV to Google Drive: {gdrive_path}")
        except Exception as exc:
            print(f"Warning: failed to copy to Google Drive: {exc}")

    shutil.rmtree(temp_dir, ignore_errors=True)
    print("Temporary files removed.")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
