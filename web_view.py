#!/usr/bin/env python3
"""Dashboard and CSV viewer for glowing-giggle crawl outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

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
          </div>
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
