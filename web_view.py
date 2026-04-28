#!/usr/bin/env python3
"""Dashboard and CSV viewer for glowing-giggle crawl outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import os
import subprocess

import pandas as pd
from flask import Flask, abort, redirect, render_template_string, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_DIRS: Dict[str, Path] = {
    "tweets": BASE_DIR / "tweets-data",
    "threads": BASE_DIR / "thread-comments",
}

app = Flask(__name__)

INDEX_PAGE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>glowing-giggle Dashboard</title>
    <style>
      :root {
        color-scheme: light;
        font-family: "Segoe UI", system-ui, sans-serif;
        background: #f2f7fb;
        color: #111827;
      }
      * { box-sizing: border-box; }
      body { margin: 0; padding: 0; }
      .page-shell { max-width: 1200px; margin: 0 auto; padding: 24px; }
      .hero { display: grid; gap: 16px; margin-bottom: 28px; }
      .hero h1 { margin: 0; font-size: clamp(2rem, 2.4vw, 3rem); letter-spacing: -0.04em; }
      .hero p { margin: 0; color: #475569; line-height: 1.75; max-width: 760px; }
      .eyebrow { text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.2em; color: #0f172a; opacity: 0.75; margin-bottom: 6px; }
      .button-row { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }
      .button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 12px 18px; border-radius: 999px; border: none; background: #2563eb; color: white; text-decoration: none; font-weight: 600; transition: transform 0.2s ease, background 0.2s ease; }
      .button:hover { background: #1d4ed8; transform: translateY(-1px); }
      .button-secondary { background: #e2e8f0; color: #0f172a; }
      .button-secondary:hover { background: #cbd5e1; }
      .input-row { display: grid; gap: 12px; margin-top: 16px; }
      .form-field { display: grid; gap: 8px; }
      .form-field label { font-size: 0.95rem; color: #475569; }
      .form-field input { width: 100%; border: 1px solid #d1d5db; border-radius: 14px; padding: 12px 14px; font-size: 1rem; background: white; color: #111827; }
      .form-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }
      .control-note { font-size: 0.95rem; color: #64748b; margin-top: 8px; }
      .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px; margin-bottom: 24px; }
      .stat-card, .section-card { background: white; border-radius: 24px; box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08); padding: 22px; }
      .stat-card h3 { margin: 0 0 10px; font-size: 0.95rem; color: #475569; text-transform: uppercase; letter-spacing: 0.08em; }
      .stat-card p { margin: 0; font-size: clamp(1.6rem, 2vw, 2.3rem); font-weight: 700; color: #111827; }
      .section-card h2 { margin-top: 0; font-size: 1.4rem; }
      .table-wrapper { overflow-x: auto; }
      table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 16px; }
      th, td { text-align: left; padding: 14px 16px; }
      th { color: #475569; font-size: 0.95rem; letter-spacing: 0.02em; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; }
      td { border-bottom: 1px solid #f1f5f9; color: #0f172a; }
      tr:hover td { background: #f8fafc; }
      a { color: #2563eb; text-decoration: none; }
      a:hover { text-decoration: underline; }
      .empty-state { padding: 20px 16px; border-radius: 16px; background: #f8fafc; color: #475569; }
      .tag { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px; background: #eef2ff; color: #4338ca; font-size: 0.92rem; font-weight: 600; }
      @media (min-width: 640px) { .hero { grid-template-columns: 1.5fr 1fr; align-items: center; } }
    </style>
  </head>
  <body>
    <div class="page-shell">
      <header class="hero">
        <div>
          <p class="eyebrow">glowing-giggle dashboard</p>
          <h1>CSV Crawl Summary & Preview</h1>
          <p>Review the latest tweet and thread comment exports, check key dataset counts, and open any CSV directly in the browser.</p>
          <div class="button-row">
            <a class="button" href="#datasets">Browse datasets</a>
            <a class="button button-secondary" href="{{ url_for('index') }}">Refresh</a>
            <a class="button button-secondary" href="{{ url_for('crawl_target', target='threads') }}">Crawl thread comments</a>
          </div>
          <form class="input-row" action="{{ url_for('crawl_target', target='tweets') }}" method="get">
            <div class="form-grid">
              <div class="form-field">
                <label for="keyword">Keyword pencarian</label>
                <input id="keyword" name="keyword" type="text" placeholder="contoh: Kemenlu OR @menluRI" value="{{ request.args.get('keyword', '') }}" />
              </div>
              <div class="form-field">
                <label for="start_year">Tahun mulai</label>
                <input id="start_year" name="start_year" type="number" min="2008" max="2100" placeholder="2024" value="{{ request.args.get('start_year', '2024') }}" />
              </div>
              <div class="form-field">
                <label for="end_year">Tahun selesai</label>
                <input id="end_year" name="end_year" type="number" min="2008" max="2100" placeholder="2025" value="{{ request.args.get('end_year', '2025') }}" />
              </div>
            </div>
            <div class="button-row" style="margin-top: 12px;">
              <button class="button" type="submit">Crawl tweets</button>
            </div>
          </form>
          <form class="input-row" action="{{ url_for('crawl_target', target='threads') }}" method="get">
            <div class="section-card" style="padding: 18px; margin-top: 12px;">
              <h2 style="margin-top: 0;">Crawl thread comments</h2>
              <div class="form-grid">
                <div class="form-field">
                  <label for="input_csv">Path CSV input</label>
                  <input id="input_csv" name="input_csv" type="text" placeholder="tweets-data/KemenluDynamicStance...part1.csv" value="" />
                </div>
                <div class="form-field">
                  <label for="max_threads">Max threads</label>
                  <input id="max_threads" name="max_threads" type="number" min="0" placeholder="0 = all" value="0" />
                </div>
                <div class="form-field">
                  <label for="tweet_limit">Limit per thread</label>
                  <input id="tweet_limit" name="tweet_limit" type="number" min="1" placeholder="15000" value="15000" />
                </div>
                <div class="form-field">
                  <label for="gdrive_dir">Google Drive folder (optional)</label>
                  <input id="gdrive_dir" name="gdrive_dir" type="text" placeholder="/content/drive/MyDrive/dataset/TH/komen/" value="" />
                </div>
              </div>
              <div class="button-row" style="margin-top: 16px;">
                <button class="button" type="submit">Start comments crawl</button>
              </div>
              <p class="control-note">Isi path CSV yang memuat kolom <code>tweet_url</code>. Jika dibiarkan kosong, gunakan environment <code>INPUT_CSV_PATH</code>.</p>
            </div>
          </form>
        </div>
      </header>

      <div class="stats-grid">
        <div class="stat-card">
          <h3>Total CSV files</h3>
          <p>{{ summary.total_files }}</p>
        </div>
        <div class="stat-card">
          <h3>Total rows available</h3>
          <p>{{ summary.total_rows }}</p>
        </div>
        <div class="stat-card">
          <h3>Tweet CSV files</h3>
          <p>{{ summary.tweets_files }}</p>
        </div>
        <div class="stat-card">
          <h3>Thread CSV files</h3>
          <p>{{ summary.threads_files }}</p>
        </div>
      </div>

      {% for label, files in files_by_dir.items() %}
        <section class="section-card" id="datasets">
          <div style="display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; flex-wrap: wrap;">
            <div>
              <h2>{{ label }}</h2>
              <p style="margin: 0; color: #475569;">{{ files|length }} CSV file{{ 's' if files|length != 1 }}</p>
            </div>
            {% if files %}
              <span class="tag">Latest: {{ files[0].name }}</span>
            {% endif %}
          </div>

          {% if files %}
            <div class="table-wrapper">
              <table>
                <thead>
                  <tr><th>File</th><th>Rows</th><th>Columns</th><th>Action</th></tr>
                </thead>
                <tbody>
                  {% for file in files %}
                    <tr>
                      <td>{{ file.name }}</td>
                      <td>{{ file.row_count }}</td>
                      <td>{{ file.column_count }}</td>
                      <td><a href="{{ url_for('view_file', directory=label, filename=file.name) }}">View</a></td>
                    </tr>
                  {% endfor %}
                </tbody>
              </table>
            </div>
          {% else %}
            <div class="empty-state">
              No CSV files found in <strong>{{ label }}</strong>. Place CSV exports in the corresponding directory and refresh.
            </div>
          {% endif %}
        </section>
      {% endfor %}
    </div>
  </body>
</html>
"""

VIEW_PAGE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Viewing {{ filename }}</title>
    <style>
      :root {
        color-scheme: light;
        font-family: "Segoe UI", system-ui, sans-serif;
        background: #f2f7fb;
        color: #111827;
      }
      body { margin: 0; padding: 0; }
      .page-shell { max-width: 1200px; margin: 0 auto; padding: 24px; }
      .panel { background: white; border-radius: 24px; box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08); padding: 24px; }
      h1 { margin: 0 0 12px; font-size: clamp(1.8rem, 2.3vw, 2.6rem); }
      p { margin: 8px 0; color: #475569; line-height: 1.7; }
      .meta { display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 18px; }
      .meta strong { color: #0f172a; }
      a { color: #2563eb; text-decoration: none; }
      a:hover { text-decoration: underline; }
      .table-wrapper { overflow-x: auto; }
      table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 20px; }
      th, td { text-align: left; padding: 14px 16px; }
      th { background: #f8fafc; color: #475569; font-size: 0.9rem; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; }
      td { border-bottom: 1px solid #f1f5f9; color: #0f172a; }
      tr:hover td { background: #f8fafc; }
      .empty-state { padding: 20px; border-radius: 16px; background: #f8fafc; color: #475569; }
    </style>
  </head>
  <body>
    <div class="page-shell">
      <div class="panel">
        <h1>Viewing {{ filename }}</h1>
        <div class="meta">
          <p><strong>Directory:</strong> {{ directory }}</p>
          <p><strong>Rows:</strong> {{ row_count }}</p>
          <p><strong>Columns:</strong> {{ column_count }}</p>
          <p><a href="{{ url_for('index') }}">Back to dashboard</a></p>
        </div>

        {% if rows %}
          <div class="table-wrapper">
            <table>
              <thead>
                <tr>
                  {% for column in columns %}
                    <th>{{ column }}</th>
                  {% endfor %}
                </tr>
              </thead>
              <tbody>
                {% for row in rows %}
                  <tr>
                    {% for value in row %}
                      <td>{{ value }}</td>
                    {% endfor %}
                  </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        {% else %}
          <div class="empty-state">
            No preview rows available for this file.
          </div>
        {% endif %}
      </div>
    </div>
  </body>
</html>
"""

CRAWL_PAGE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Crawl {{ target_name }}</title>
    <style>
      :root {
        color-scheme: light;
        font-family: "Segoe UI", system-ui, sans-serif;
        background: #f2f7fb;
        color: #111827;
      }
      body { margin: 0; padding: 0; }
      .page-shell { max-width: 900px; margin: 0 auto; padding: 24px; }
      .panel { background: white; border-radius: 24px; box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08); padding: 24px; }
      h1 { margin-top: 0; font-size: clamp(1.8rem, 2.3vw, 2.6rem); }
      p { color: #475569; line-height: 1.7; }
      pre { background: #f8fafc; border-radius: 16px; padding: 18px; overflow-x: auto; white-space: pre-wrap; word-break: break-word; }
      a { color: #2563eb; text-decoration: none; }
      a:hover { text-decoration: underline; }
      .status { display: inline-flex; align-items: center; gap: 10px; padding: 12px 16px; border-radius: 14px; background: #e0f2fe; color: #0c4a6e; margin: 16px 0; }
      .error { background: #fee2e2; color: #991b1b; }
    </style>
  </head>
  <body>
    <div class="page-shell">
      <div class="panel">
        <h1>Crawl {{ target_name }}</h1>
        <p>{{ message }}</p>
        <div class="status {{ 'error' if error else '' }}">
          <strong>Status:</strong> {{ status }}</div>
        <p><strong>Log file:</strong> {{ log_file }}</p>
        <p><a href="{{ url_for('index') }}">Back to dashboard</a></p>
      </div>
    </div>
  </body>
</html>
"""

CRAWL_SCRIPTS: Dict[str, str] = {
    "tweets": "twitter_crawler.py",
    "threads": "twitter_thread_comments.py",
}

CRAWL_LOG_DIR = BASE_DIR / "crawl-logs"


def ensure_log_dir() -> None:
    CRAWL_LOG_DIR.mkdir(exist_ok=True)


def start_crawl(
    target: str,
    keyword: str = "",
    start_year: str = "",
    end_year: str = "",
    input_csv: str = "",
    max_threads: str = "",
    tweet_limit: str = "",
    output_dir: str = "",
    gdrive_dir: str = "",
) -> tuple[str, str, bool]:
    script_name = CRAWL_SCRIPTS.get(target)
    if not script_name:
        raise ValueError("Unsupported crawl target.")

    script_path = BASE_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Crawler script not found: {script_name}")

    env = os.environ.copy()
    if target == "tweets":
        if keyword or start_year or end_year:
            query_text = keyword.strip() or '("Kemenlu" OR "@menluRI")'
            if start_year or end_year:
                start = start_year or end_year
                end = end_year or start_year
                query_text = f"{query_text} since:{start}-01-01 until:{end}-12-31"
            if "lang:" not in query_text:
                query_text = f"{query_text} lang:id"
            env["SEARCH_QUERIES"] = query_text
    elif target == "threads":
        if input_csv:
            env["INPUT_CSV_PATH"] = input_csv.strip()
        if max_threads:
            env["MAX_THREADS"] = max_threads.strip()
        if tweet_limit:
            env["TWEET_LIMIT"] = tweet_limit.strip()
        if output_dir:
            env["OUTPUT_DIR"] = output_dir.strip()
        if gdrive_dir:
            env["GDRIVE_DIR"] = gdrive_dir.strip()

    ensure_log_dir()
    log_path = CRAWL_LOG_DIR / f"{target}_crawl.log"
    log_handle = open(log_path, "a", encoding="utf-8")
    subprocess.Popen(
        ["python3", str(script_path)],
        cwd=str(BASE_DIR),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        env=env,
    )

    return script_name, log_path.name, True


def list_csv_files() -> Dict[str, List[dict]]:
    result: Dict[str, List[dict]] = {}
    for label, path in DATA_DIRS.items():
        entries: List[dict] = []
        if not path.exists():
            result[label] = entries
            continue

        csv_paths = sorted(path.glob("*.csv"), reverse=True)
        for csv_path in csv_paths:
            row_count, column_count = get_csv_metadata(csv_path)
            entries.append({
                "name": csv_path.name,
                "row_count": row_count,
                "column_count": column_count,
            })
        result[label] = entries
    return result


def build_dashboard_summary(files_by_dir: Dict[str, List[dict]]) -> dict:
    tweets_files = len(files_by_dir.get("tweets", []))
    threads_files = len(files_by_dir.get("threads", []))
    total_rows = sum(file["row_count"] for files in files_by_dir.values() for file in files)

    return {
        "total_files": tweets_files + threads_files,
        "total_rows": total_rows,
        "tweets_files": tweets_files,
        "threads_files": threads_files,
    }


def get_csv_metadata(csv_path: Path) -> tuple[int, int]:
    try:
        with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
            row_count = sum(1 for _ in f) - 1
        df = pd.read_csv(csv_path, nrows=0)
        return max(row_count, 0), len(df.columns)
    except Exception:
        return 0, 0


def resolve_csv_path(directory: str, filename: str) -> Path:
    if directory not in DATA_DIRS:
        raise FileNotFoundError("Directory not permitted.")
    target_dir = DATA_DIRS[directory]
    target_path = (target_dir / filename).resolve()
    if not target_path.exists() or target_path.parent != target_dir.resolve():
        raise FileNotFoundError("File not found.")
    return target_path


@app.route("/")
def index() -> str:
    files_by_dir = list_csv_files()
    summary = build_dashboard_summary(files_by_dir)
    return render_template_string(INDEX_PAGE, files_by_dir=files_by_dir, summary=summary)


@app.route("/crawl/<target>")
def crawl_target(target: str) -> str:
    keyword = request.args.get("keyword", "").strip()
    start_year = request.args.get("start_year", "").strip()
    end_year = request.args.get("end_year", "").strip()
    input_csv = request.args.get("input_csv", "").strip()
    max_threads = request.args.get("max_threads", "").strip()
    tweet_limit = request.args.get("tweet_limit", "").strip()
    output_dir = request.args.get("output_dir", "").strip()
    gdrive_dir = request.args.get("gdrive_dir", "").strip()

    try:
        script_name, log_file, started = start_crawl(
            target,
            keyword=keyword,
            start_year=start_year,
            end_year=end_year,
            input_csv=input_csv,
            max_threads=max_threads,
            tweet_limit=tweet_limit,
            output_dir=output_dir,
            gdrive_dir=gdrive_dir,
        )
        status = "Crawl started successfully." if started else "Crawl could not start."
        message = f"The crawler script {script_name} is running in the background."
        if target == "tweets" and keyword:
            message += f" Search keyword: {keyword}."
        if target == "tweets" and start_year and end_year:
            message += f" Range: {start_year}–{end_year}."
        if target == "threads" and input_csv:
            message += f" Input CSV: {input_csv}."
        if target == "threads" and max_threads:
            message += f" Max threads: {max_threads}."
        error = False
    except FileNotFoundError as exc:
        status = "Crawler script missing."
        message = str(exc)
        log_file = "n/a"
        error = True
    except ValueError as exc:
        status = "Invalid crawl target."
        message = str(exc)
        log_file = "n/a"
        error = True
    except Exception as exc:
        status = "Failed to start crawl."
        message = str(exc)
        log_file = "n/a"
        error = True

    return render_template_string(
        CRAWL_PAGE,
        target_name=target.replace("_", " ").title(),
        status=status,
        message=message,
        log_file=log_file,
        error=error,
    )


@app.route("/view")
def view_file() -> str:
    directory = request.args.get("directory", "")
    filename = request.args.get("filename", "")
    if not filename:
        return redirect(url_for("index"))

    try:
        csv_path = resolve_csv_path(directory, filename)
    except FileNotFoundError:
        abort(404)

    df = pd.read_csv(csv_path, dtype=str, nrows=200)
    row_count, column_count = get_csv_metadata(csv_path)
    rows = df.fillna("").values.tolist()
    columns = df.columns.tolist()

    return render_template_string(
        VIEW_PAGE,
        filename=filename,
        directory=directory,
        row_count=row_count,
        column_count=column_count,
        preview_rows=min(len(rows), 200),
        columns=columns,
        rows=rows,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
