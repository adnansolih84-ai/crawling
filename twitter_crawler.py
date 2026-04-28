#!/usr/bin/env python3
"""Twitter/X crawler script for glowing-giggle.

This script uses `npx tweet-harvest` to collect tweets, saves output to
`./tweets-data/`, filters results to Bahasa Indonesia, and optionally
copies the final CSV to a mounted Google Drive path.

Usage:
  export TWITTER_AUTH_TOKEN=...
  python3 twitter_crawler.py

Optional environment variables:
  SEARCH_QUERIES    Comma-separated query strings
  OUTPUT_DIR        Output directory for local CSV files
  GDRIVE_DIR        Optional Google Drive directory to copy final CSV into
  TWEET_LIMIT       Number of tweets per query (default: 15000)
"""

import csv
import os
import shlex
import subprocess
import sys
from datetime import datetime

import pandas as pd
from langdetect import detect, LangDetectException

TWITTER_AUTH_TOKEN = os.environ.get("TWITTER_AUTH_TOKEN")
DEFAULT_OUTPUT_DIR = "tweets-data"
DEFAULT_GDRIVE_DIR = os.environ.get("GDRIVE_DIR", "")
DEFAULT_LIMIT = int(os.environ.get("TWEET_LIMIT", "15000"))

DEFAULT_QUERIES = [
    '("Kemenlu" OR "@menluRI") since:2024-01-01 until:2025-12-31 lang:id'
]


def run_command(command: str) -> int:
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    return result.returncode


def load_queries() -> list[str]:
    queries = os.environ.get("SEARCH_QUERIES")
    if not queries:
        return DEFAULT_QUERIES

    # split on comma, but allow commas inside quoted strings if needed
    return [q.strip() for q in queries.split(",") if q.strip()]


def build_output_filename(base: str, part: int) -> str:
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    return f"{base}_{timestamp}_part{part}.csv"


def detect_indonesian(text: str) -> bool:
    try:
        return detect(text) == "id"
    except LangDetectException:
        return False


def read_tweet_file(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    if os.path.getsize(path) == 0:
        return pd.DataFrame()

    try:
        return pd.read_csv(path, dtype=str)
    except Exception as exc:
        raise RuntimeError(f"Failed reading CSV {path}: {exc}") from exc


def save_dataframe(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows to {path}")


def copy_to_gdrive(src: str, dest_dir: str) -> str:
    if not dest_dir:
        raise ValueError("GDRIVE_DIR is not set.")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, os.path.basename(src))
    df = pd.read_csv(src, dtype=str)
    df.to_csv(dest, index=False)
    return dest


def main() -> int:
    if not TWITTER_AUTH_TOKEN:
        print("Error: TWITTER_AUTH_TOKEN environment variable is required.")
        return 1

    output_dir = os.environ.get("OUTPUT_DIR", DEFAULT_OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)

    queries = load_queries()
    if not queries:
        print("Error: No search queries provided.")
        return 1

    print("Twitter/X crawler starting...")
    print(f"Output directory: {output_dir}")
    print(f"Tweet limit per query: {DEFAULT_LIMIT}")
    print(f"Query count: {len(queries)}")

    collected_frames: list[pd.DataFrame] = []

    for index, query in enumerate(queries, start=1):
        filename = build_output_filename("KemenluDynamicStance", index)
        local_path = os.path.join(output_dir, filename)

        command = (
            f'npx -y tweet-harvest@2.6.1 -o {shlex.quote(local_path)} '
            f'-s {shlex.quote(query)} --tab LATEST -l {DEFAULT_LIMIT} '
            f'--token {shlex.quote(TWITTER_AUTH_TOKEN)}'
        )

        exit_code = run_command(command)
        if exit_code != 0:
            print(f"Warning: tweet-harvest exited with code {exit_code} for query #{index}")
            continue

        try:
            df_temp = read_tweet_file(local_path)
        except Exception as exc:
            print(f"Warning: could not read file {local_path}: {exc}")
            continue

        if df_temp.empty:
            print(f"No tweets found for query #{index}.")
            continue

        print(f"Loaded {len(df_temp)} rows from {local_path}")
        collected_frames.append(df_temp)

    if not collected_frames:
        print("No tweet data collected. Exiting.")
        return 0

    df = pd.concat(collected_frames, ignore_index=True)
    print(f"Total tweets before language filter: {len(df)}")

    text_column = "full_text" if "full_text" in df.columns else "tweet" if "tweet" in df.columns else None
    if not text_column:
        print("Error: No tweet text column found (expected 'full_text' or 'tweet').")
        return 1

    df[text_column] = df[text_column].fillna("")
    df["is_indonesian"] = df[text_column].apply(detect_indonesian)
    df_filtered = df[df["is_indonesian"]].drop(columns=["is_indonesian"])
    print(f"Total tweets after Bahasa Indonesia filter: {len(df_filtered)}")

    final_name = build_output_filename("KemenluDynamicStance_FULL_ID", 0)
    final_local_path = os.path.join(output_dir, final_name)
    save_dataframe(df_filtered, final_local_path)

    if DEFAULT_GDRIVE_DIR:
        try:
            final_gdrive_path = copy_to_gdrive(final_local_path, DEFAULT_GDRIVE_DIR)
            print(f"Copied filtered CSV to Google Drive: {final_gdrive_path}")
        except Exception as exc:
            print(f"Warning: failed to copy to Google Drive: {exc}")

    print("Done. Data is ready for topic modeling and stance analysis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
