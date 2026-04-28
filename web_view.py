#!/usr/bin/env python3
"""Simple web viewer for glowing-giggle CSV results."""

from __future__ import annotations

import os
from glob import glob
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
    <title>glowing-giggle CSV Viewer</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 24px; }
      h1, h2 { color: #111; }
      table { border-collapse: collapse; width: 100%; margin-top: 12px; }
      th, td { border: 1px solid #ddd; padding: 8px; }
      th { background: #f2f2f2; }
      a { color: #0066cc; text-decoration: none; }
      a:hover { text-decoration: underline; }
      .box { padding: 16px; border: 1px solid #ccc; margin-bottom: 16px; border-radius: 8px; background: #fafafa; }
    </style>
  </head>
  <body>
    <h1>glowing-giggle CSV Viewer</h1>
    <p>Browse available tweet and thread comment CSV files in the repository.</p>

    {% for label, files in files_by_dir.items() %}
      <div class="box">
        <h2>{{ label }}</h2>
        {% if files %}
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
        {% else %}
          <p>No CSV files found in <code>{{ label }}</code>.</p>
        {% endif %}
      </div>
    {% endfor %}
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
      body { font-family: Arial, sans-serif; margin: 24px; }
      h1, h2 { color: #111; }
      table { border-collapse: collapse; width: 100%; margin-top: 12px; }
      th, td { border: 1px solid #ddd; padding: 8px; }
      th { background: #f2f2f2; }
      a { color: #0066cc; text-decoration: none; }
      a:hover { text-decoration: underline; }
      pre { background: #f7f7f7; padding: 12px; border-radius: 6px; overflow-x: auto; }
    </style>
  </head>
  <body>
    <h1>Viewing {{ filename }}</h1>
    <p><strong>Directory:</strong> {{ directory }}</p>
    <p><strong>Rows:</strong> {{ row_count }}, <strong>Columns:</strong> {{ column_count }}</p>
    <p><a href="{{ url_for('index') }}">Back to file list</a></p>

    <h2>Preview (first {{ preview_rows }} rows)</h2>
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
  </body>
</html>
"""


def list_csv_files() -> Dict[str, List[dict]]:
    result = {}
    for label, path in DATA_DIRS.items():
        rows = []
        if not path.exists():
            result[label] = rows
            continue

        csv_paths = sorted(path.glob("*.csv"), reverse=True)
        for csv_path in csv_paths:
            row_count, column_count = get_csv_metadata(csv_path)
            rows.append({
                "name": csv_path.name,
                "row_count": row_count,
                "column_count": column_count,
            })
        result[label] = rows
    return result


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
    return render_template_string(INDEX_PAGE, files_by_dir=files_by_dir)


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
