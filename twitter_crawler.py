#!/usr/bin/env python3
"""Twitter/X crawler for glowing-giggle.

This script runs `tweet-harvest` to collect tweets, filters results to Indonesian,
and saves the final CSV output locally and optionally to a Google Drive directory.

Environment variables:
  TWITTER_AUTH_TOKEN  - required Twitter/X bearer token
  SEARCH_QUERIES      - optional comma-separated list of full queries
  SEARCH_KEYWORD      - optional search keywords if SEARCH_QUERIES is not set
  START_YEAR          - optional start year for the date range
  END_YEAR            - optional end year for the date range
  OUTPUT_DIR          - output directory for CSV files
  GDRIVE_DIR          - optional Google Drive directory to copy the final CSV into
  TWEET_LIMIT         - number of tweets per query (default: 15000)
"""

import os
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd
from langdetect import detect, LangDetectException

TWITTER_AUTH_TOKEN = os.environ.get("TWITTER_AUTH_TOKEN")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "tweets-data")
GDRIVE_DIR = os.environ.get("GDRIVE_DIR", "")
DEFAULT_LIMIT = int(os.environ.get("TWEET_LIMIT", "15000"))
SEARCH_QUERIES = os.environ.get("SEARCH_QUERIES", "").strip()
SEARCH_KEYWORD = os.environ.get("SEARCH_KEYWORD", "").strip()
START_YEAR = os.environ.get("START_YEAR", "").strip()
END_YEAR = os.environ.get("END_YEAR", "").strip()

DEFAULT_QUERIES = [
    '("Kemenlu" OR "@menluRI") since:2024-01-01 until:2025-12-31 lang:id'
]


def build_query_list() -> List[str]:
    if SEARCH_QUERIES:
        return [q.strip() for q in SEARCH_QUERIES.split(",") if q.strip()]

    if SEARCH_KEYWORD or START_YEAR or END_YEAR:
        query = SEARCH_KEYWORD or '("Kemenlu" OR "@menluRI")'

        if START_YEAR or END_YEAR:
            start = START_YEAR or END_YEAR
            end = END_YEAR or START_YEAR
            query = f"{query} since:{start}-01-01 until:{end}-12-31"

        if "lang:" not in query:
            query = f"{query} lang:id"

        return [query.strip()]

    return DEFAULT_QUERIES


def run_command(command: str) -> int:
    print(f"Running: {command}")
    return subprocess.run(command, shell=True).returncode


def build_output_filename(base: str, part: int) -> str:
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    return f"{base}_{timestamp}_part{part}.csv"


def detect_indonesian(text: str) -> bool:
    try:
        return detect(text) == "id"
    except LangDetectException:
        return False


def read_tweet_file(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.stat().st_size == 0:
        return pd.DataFrame()

    return pd.read_csv(path, dtype=str)


def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows to {path}")


def copy_to_gdrive(src: Path, dest_dir: str) -> Path:
    os.makedirs(dest_dir, exist_ok=True)
    dest = Path(dest_dir) / src.name
    df = pd.read_csv(src, dtype=str)
    df.to_csv(dest, index=False)
    return dest


def main() -> int:
    if not TWITTER_AUTH_TOKEN:
        print("Error: TWITTER_AUTH_TOKEN environment variable is required.")
        return 1

    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    queries = build_query_list()
    if not queries:
        print("Error: No queries were defined.")
        return 1

    print("Twitter/X crawler starting...")
    print(f"Output directory: {output_dir}")
    print(f"Tweet limit per query: {DEFAULT_LIMIT}")
    print(f"Query count: {len(queries)}")

    collected: List[pd.DataFrame] = []
    for index, query in enumerate(queries, start=1):
        filename = build_output_filename("KemenluDynamicStance", index)
        local_path = output_dir / filename

        command = (
            f'npx -y tweet-harvest@2.6.1 -o {shlex.quote(str(local_path))} '
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
        collected.append(df_temp)

    if not collected:
        print("No tweet data collected. Exiting.")
        return 0

    df = pd.concat(collected, ignore_index=True)
    print(f"Total tweets before language filter: {len(df)}")

    text_column = "full_text" if "full_text" in df.columns else "tweet" if "tweet" in df.columns else None
    if not text_column:
        print("Error: No tweet text column found (expected 'full_text' or 'tweet').")
        return 1

    df[text_column] = df[text_column].fillna("")
    df["is_indonesian"] = df[text_column].apply(detect_indonesian)
    df_filtered = df[df["is_indonesian"]].drop(columns=["is_indonesian"])
    print(f"Total tweets after Bahasa Indonesia filter: {len(df_filtered)}")

    final_name = f"KemenluDynamicStance_FULL_ID_{datetime.now().strftime('%d%m%Y_%H%M%S')}.csv"
    final_local_path = output_dir / final_name
    save_dataframe(df_filtered, final_local_path)

    if GDRIVE_DIR:
        try:
            final_gdrive_path = copy_to_gdrive(final_local_path, GDRIVE_DIR)
            print(f"Copied filtered CSV to Google Drive: {final_gdrive_path}")
        except Exception as exc:
            print(f"Warning: failed to copy to Google Drive: {exc}")

    print("Done. Data is ready for topic modeling and stance analysis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
