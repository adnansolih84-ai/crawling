#!/usn/env python3
"""Dashboard and CSV viewer for glowing-giggle crawl outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import os
import subprocess
from collections import deque

from dotenv import load_dotenv
import pandas as pd
from flask import Flask, abort, redirect, render_template_string, request, send_file, url_for

# Load .env from script directory
load_dotenv(Path(__file__).resolve().parent / ".env")

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
    <title>X-Insights Crawler Panel</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" integrity="sha512-H4s3iCkT2R+s4xqyTnUSvkpOTn6fiMpYt32kRm1XQnZcj2/jz4WBOJjCustPaG7j4ZpDYEW5nAXjCeuX7+LZ2w==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    <style>
      :root {
        color-scheme: light;
        font-family: 'Inter', system-ui, sans-serif;
        background: #eef5fd;
        color: #0f172a;
      }
      * { box-sizing: border-box; }
      html, body { margin: 0; padding: 0; min-height: 100%; }
      body { background: linear-gradient(180deg, #f8fbff 0%, #eef5fd 100%); }
      .page-shell { width: min(1200px, 100%); margin: 0 auto; padding: 24px 20px 40px; }
      .topbar { display: grid; gap: 16px; margin-bottom: 24px; }
      .eyebrow { margin: 0; text-transform: uppercase; letter-spacing: 0.24em; font-size: 0.8rem; color: #2563eb; font-weight: 700; }
      h1 { margin: 0; font-size: clamp(2rem, 2.6vw, 2.8rem); line-height: 1.05; }
      .intro { margin: 12px 0 0; max-width: 760px; color: #475569; line-height: 1.8; }
      .tab-list { display: flex; flex-wrap: wrap; gap: 12px; }
      .tab-button { appearance: none; border: none; border-radius: 999px; padding: 12px 18px; font-size: 0.98rem; cursor: pointer; background: #e2e8f0; color: #334155; transition: all 0.2s ease; display: inline-flex; align-items: center; gap: 10px; }
      .tab-button.active { background: #2563eb; color: white; box-shadow: 0 16px 40px rgba(37, 99, 235, 0.18); }
      .tab-panel { display: none; animation: fade-in 0.18s ease-in-out; }
      .tab-panel.active { display: block; }
      .section-card { background: white; border-radius: 28px; box-shadow: 0 32px 90px rgba(15, 23, 42, 0.08); padding: 26px; margin-bottom: 22px; }
      .panel-grid { display: grid; gap: 18px; }
      .stats-grid { display: grid; gap: 18px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin-bottom: 0; }
      .stat-card { min-height: 120px; padding: 24px; display: grid; gap: 10px; }
      .stat-card h3 { margin: 0; font-size: 0.9rem; letter-spacing: 0.1em; text-transform: uppercase; color: #64748b; }
      .stat-card p { margin: 0; font-size: clamp(1.8rem, 2.2vw, 2.4rem); font-weight: 700; color: #0f172a; }
      .form-grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin-top: 18px; }
      .form-field { display: grid; gap: 8px; }
      .form-field label { color: #475569; font-size: 0.95rem; }
      .form-field input { width: 100%; border: 1px solid #cbd5e1; border-radius: 16px; padding: 14px 16px; font-size: 1rem; background: #f8fafc; color: #0f172a; }
      .form-field input:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.08); }
      .form-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 20px; }
      .button { display: inline-flex; align-items: center; justify-content: center; gap: 10px; padding: 14px 20px; border-radius: 14px; border: none; cursor: pointer; font-weight: 700; transition: transform 0.18s ease, background 0.18s ease; }
      .button.primary { background: #2563eb; color: white; }
      .button.primary:hover { background: #1d4ed8; transform: translateY(-1px); }
      .button.secondary { background: #e2e8f0; color: #334155; }
      .button.secondary:hover { background: #cbd5e1; }
      .help-box { display: flex; gap: 14px; align-items: start; padding: 18px; border-radius: 18px; background: #eff6ff; border: 1px solid #dbeafe; color: #1d4ed8; margin-top: 16px; }
      .help-box strong { color: #1e40af; }
      .table-wrapper { overflow-x: auto; }
      table { width: 100%; border-collapse: collapse; margin-top: 18px; }
      th, td { padding: 14px 16px; text-align: left; }
      th { background: #f8fafc; color: #475569; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.08em; border-bottom: 1px solid #e2e8f0; }
      td { border-bottom: 1px solid #f1f5f9; color: #0f172a; }
      tr:hover td { background: #f8fafc; }
      .tag { display: inline-flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 999px; background: #e0f2fe; color: #1d4ed8; font-size: 0.9rem; }
      .empty-state { padding: 20px 18px; border-radius: 18px; background: #f8fafc; color: #475569; }
      @keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
      @media (max-width: 720px) { .form-grid { grid-template-columns: 1fr; } .tab-list { justify-content: flex-start; } }
    </style>
  </head>
  <body>
    <div class="page-shell">
      <div class="topbar">
        <div>
          <p class="eyebrow">X-Insights Crawler Panel</p>
          <h1>Dashboard Crawling Twitter/X</h1>
          <p class="intro">Navigation sudah disederhanakan dengan tab, sehingga Anda dapat fokus ke Crawl Tweets atau Crawl Comments tanpa tampilan yang berantakan.</p>
        </div>
        <div class="tab-list">
          <button type="button" class="tab-button active" data-tab="dashboard"><i class="fa-solid fa-chart-simple"></i> Dashboard</button>
          <button type="button" class="tab-button" data-tab="crawl-tweets"><i class="fa-solid fa-magnifying-glass"></i> Crawl Tweets</button>
          <button type="button" class="tab-button" data-tab="crawl-comments"><i class="fa-solid fa-comments"></i> Crawl Comments</button>
        </div>
      </div>

      <section id="dashboard" class="tab-panel active">
        <div class="section-card panel-grid">
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
        </div>

        <div class="section-card">
          <div style="display:flex; gap:16px; align-items:center; flex-wrap:wrap; justify-content:space-between;">
            <div>
              <h2>Dataset yang tersedia</h2>
              <p style="margin:0; color:#475569;">Pilih file untuk melakukan preview atau jalankan crawl baru dari tab yang sesuai.</p>
            </div>
            <a class="button secondary" href="{{ url_for('index') }}"><i class="fa-solid fa-arrow-rotate-right"></i> Refresh</a>
          </div>

          {% for label, files in files_by_dir.items() %}
            <div style="margin-top: 24px;">
              <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;margin-bottom:12px;">
                <h3 style="margin:0;">{{ label }}</h3>
                {% if files %}<span class="tag">Latest: {{ files[0].name }}</span>{% endif %}
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
                          <td>
                            <a href="{{ url_for('index', preview_directory=label, preview_filename=file.name) }}">Preview</a>
                            ·
                            <a href="{{ url_for('view_file', directory=label, filename=file.name) }}">View</a>
                            ·
                            <a href="{{ url_for('download_file', directory=label, filename=file.name) }}">Download</a>
                          </td>
                        </tr>
                      {% endfor %}
                    </tbody>
                  </table>
                </div>
              {% else %}
                <div class="empty-state">Tidak ada file CSV ditemukan di <strong>{{ label }}</strong>. Silakan download atau letakkan CSV di folder yang sesuai.</div>
              {% endif %}
            </div>
          {% endfor %}

          {% if preview and preview.columns %}
            <div class="section-card">
              <div style="display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap; margin-bottom:18px;">
                <div>
                  <h2>Preview: {{ preview.filename }}</h2>
                  <p style="margin:0; color:#475569;">Directory: <strong>{{ preview.directory }}</strong> · Rows: <strong>{{ preview.row_count }}</strong> · Columns: <strong>{{ preview.column_count }}</strong></p>
                </div>
                <a class="button secondary" href="{{ url_for('index') }}"><i class="fa-solid fa-xmark"></i> Clear Preview</a>
              </div>
              <div class="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      {% for column in preview.columns %}
                        <th>{{ column }}</th>
                      {% endfor %}
                    </tr>
                  </thead>
                  <tbody>
                    {% for row in preview.rows %}
                      <tr>
                        {% for value in row %}
                          <td>{{ value }}</td>
                        {% endfor %}
                      </tr>
                    {% endfor %}
                  </tbody>
                </table>
              </div>
            </div>
          {% elif preview %}
            <div class="section-card">
              <div class="empty-state">Preview requested for {{ preview.filename }}, but no rows are available.</div>
            </div>
          {% endif %}
        </div>
      </section>

      <section id="crawl-tweets" class="tab-panel">
        <div class="section-card">
          <div style="display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap; align-items:center;">
            <div>
              <h2>Crawl Tweets</h2>
              <p style="margin:0; color:#475569;">Masukkan keyword dan rentang tanggal penuh untuk memulai proses crawling tweet.</p>
            </div>
            <span class="tag"><i class="fa-solid fa-calendar-days"></i> Date range support</span>
          </div>

          <form action="{{ url_for('crawl_target', target='tweets') }}" method="get">
            <div class="form-grid">
              <div class="form-field">
                <label for="keyword">Keyword pencarian</label>
                <input id="keyword" name="keyword" type="text" placeholder="contoh: (Kemenlu OR @menluRI)" value="{{ request.args.get('keyword', '') }}" />
              </div>
              <div class="form-field">
                <label for="start_date">Tanggal mulai</label>
                <input id="start_date" name="start_date" type="date" value="{{ request.args.get('start_date', '2026-01-01') }}" />
              </div>
              <div class="form-field">
                <label for="end_date">Tanggal selesai</label>
                <input id="end_date" name="end_date" type="date" value="{{ request.args.get('end_date', '2026-12-31') }}" />
              </div>
              <div class="form-field">
                <label for="tweet_limit">Limit tweet per query</label>
                <input id="tweet_limit" name="tweet_limit" type="number" min="100" placeholder="15000" value="15000" />
              </div>
              <div class="form-field">
                <label for="output_dir">Output folder (optional)</label>
                <input id="output_dir" name="output_dir" type="text" placeholder="tweets-data" value="tweets-data" />
              </div>
              <div class="form-field">
                <label for="gdrive_dir">Google Drive folder (optional)</label>
                <input id="gdrive_dir" name="gdrive_dir" type="text" placeholder="/content/drive/MyDrive/dataset/TH/BT/" value="" />
              </div>
            </div>
            <div class="form-actions">
              <button class="button primary" type="submit"><i class="fa-solid fa-play"></i> Start Tweet Crawl</button>
              <button class="button secondary" type="reset"><i class="fa-solid fa-eraser"></i> Reset Form</button>
            </div>
          </form>

          <div class="help-box">
            <div><i class="fa-solid fa-circle-info"></i></div>
            <div>
              <strong>Tip:</strong> gunakan format tanggal <code>YYYY-MM-DD</code> untuk rentang waktu. Jika field kosong, crawler akan menggunakan default internal.
            </div>
          </div>
        </div>
      </section>

      <section id="crawl-comments" class="tab-panel">
        <div class="section-card">
          <div style="display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap; align-items:center;">
            <div>
              <h2>Crawl Thread Comments</h2>
              <p style="margin:0; color:#475569;">Gunakan file CSV tweet yang berisi kolom <code>tweet_url</code> untuk mengambil komentar thread berdasarkan urutan retweet tertinggi.</p>
            </div>
            <span class="tag"><i class="fa-solid fa-link"></i> thread URL</span>
          </div>

          <form action="{{ url_for('crawl_target', target='threads') }}" method="get">
            <div class="form-grid">
              <div class="form-field">
                <label for="input_csv">Path CSV input</label>
                <input id="input_csv" name="input_csv" type="text" placeholder="tweets-data/KemenluDynamicStance_part1.csv" value="" />
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
                <label for="output_dir">Output folder (optional)</label>
                <input id="output_dir" name="output_dir" type="text" placeholder="thread-comments" value="thread-comments" />
              </div>
              <div class="form-field">
                <label for="gdrive_dir">Google Drive folder (optional)</label>
                <input id="gdrive_dir" name="gdrive_dir" type="text" placeholder="/content/drive/MyDrive/dataset/TH/komen/" value="" />
              </div>
            </div>
            <div class="form-actions">
              <button class="button primary" type="submit"><i class="fa-solid fa-play"></i> Start Comments Crawl</button>
              <button class="button secondary" type="reset"><i class="fa-solid fa-eraser"></i> Reset Form</button>
            </div>
          </form>

          <div class="help-box">
            <div><i class="fa-solid fa-circle-info"></i></div>
            <div>
              <strong>Note:</strong> isi <code>INPUT_CSV_PATH</code> dengan file CSV yang berisi kolom <code>tweet_url</code>. Kosongkan untuk menggunakan variabel environment default.
            </div>
          </div>
        </div>
      </section>
    </div>

    <script>
      const tabButtons = document.querySelectorAll('.tab-button');
      const tabPanels = document.querySelectorAll('.tab-panel');
      tabButtons.forEach((button) => {
        button.addEventListener('click', () => {
          const target = button.dataset.tab;
          tabButtons.forEach((btn) => btn.classList.toggle('active', btn === button));
          tabPanels.forEach((panel) => panel.classList.toggle('active', panel.id === target));
        });
      });
    </script>
  </body>
</html>
"""

VIEW_PAGE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Viewing {{ filename }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" integrity="sha512-H4s3iCkT2R+s4xqyTnUSvkpOTn6fiMpYt32kRm1XQnZcj2/jz4WBOJjCustPaG7j4ZpDYEW5nAXjCeuX7+LZ2w==" crossorigin="anonymous" referrerpolicy="no-referrer" />
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
      .button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 10px 16px; border-radius: 12px; border: none; background: #e2e8f0; color: #334155; text-decoration: none; font-weight: 600; }
      .button.secondary { background: #e2e8f0; }
      .button.secondary:hover { background: #cbd5e1; }
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
          <p><a class="button secondary" href="{{ url_for('download_file', directory=directory, filename=filename) }}"><i class="fa-solid fa-download"></i> Download CSV</a></p>
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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" integrity="sha512-H4s3iCkT2R+s4xqyTnUSvkpOTn6fiMpYt32kRm1XQnZcj2/jz4WBOJjCustPaG7j4ZpDYEW5nAXjCeuX7+LZ2w==" crossorigin="anonymous" referrerpolicy="no-referrer" />
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
      pre { background: #f8fafc; border-radius: 16px; padding: 18px; overflow-x: auto; white-space: pre-wrap; word-break: break-word; max-height: 300px; overflow-y: auto; }
      a { color: #2563eb; text-decoration: none; }
      a:hover { text-decoration: underline; }
      .status { display: inline-flex; align-items: center; gap: 10px; padding: 12px 16px; border-radius: 14px; background: #e0f2fe; color: #0c4a6e; margin: 16px 0; }
      .error { background: #fee2e2; color: #991b1b; }
      .success { background: #dcfce7; color: #166534; }
      .info-box { display: flex; gap: 14px; align-items: start; padding: 18px; border-radius: 18px; background: #eff6ff; border: 1px solid #dbeafe; color: #1d4ed8; margin: 16px 0; }
      .info-box strong { color: #1e40af; }
      .metrics-grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); margin: 18px 0; }
      .metric-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 18px; padding: 18px; }
      .metric-card span { display: block; color: #475569; font-size: 0.95rem; margin-bottom: 10px; }
      .metric-card p { margin: 0; font-size: clamp(1.8rem, 2.2vw, 2.2rem); font-weight: 700; color: #0f172a; }
      .progress-container { margin: 20px 0; }
      .progress-bar { width: 100%; height: 20px; background: #e2e8f0; border-radius: 10px; overflow: hidden; margin: 8px 0; }
      .progress-fill { height: 100%; background: linear-gradient(90deg, #2563eb, #3b82f6); transition: width 0.3s ease; border-radius: 10px; }
      .progress-text { font-size: 0.95rem; color: #475569; text-align: center; margin-top: 4px; }
      .log-section { margin-top: 24px; }
      .log-toggle { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 16px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; width: 100%; }
      .log-toggle:hover { background: #f1f5f9; }
      .log-content { display: none; margin-top: 12px; }
      .log-content.expanded { display: block; }
      .button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 10px 16px; border-radius: 12px; border: none; background: #e2e8f0; color: #334155; text-decoration: none; font-weight: 600; cursor: pointer; }
      .button:hover { background: #cbd5e1; }
      .button.primary { background: #2563eb; color: white; }
      .button.primary:hover { background: #1d4ed8; }
      @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
      .pulse { animation: pulse 2s infinite; }
    </style>
  </head>
  <body>
    <div class="page-shell">
      <div class="panel">
        <h1><i class="fa-solid fa-spider"></i> Crawl {{ target_name }}</h1>

        <div class="info-box">
          <div><i class="fa-solid fa-circle-info"></i></div>
          <div>
            <strong>Script:</strong> <code>{{ script_name }}</code> sedang berjalan di background.
            {% if keyword %}<br><strong>Keyword:</strong> <code>{{ keyword }}</code>{% endif %}
            {% if start_date and end_date %}<br><strong>Range:</strong> {{ start_date }} – {{ end_date }}{% endif %}
            {% if input_csv %}<br><strong>Input CSV:</strong> {{ input_csv }}{% endif %}
          </div>
        </div>

        <div class="status {{ 'error' if error else 'success' if not error and started else '' }}">
          <i class="fa-solid {{ 'fa-exclamation-triangle' if error else 'fa-check-circle' if not error and started else 'fa-spinner fa-spin' }}"></i>
          <strong>Status:</strong> {{ status }}
        </div>

        {% if not error %}
        <div class="metrics-grid">
          <div class="metric-card">
            <span>Tweets terkumpul</span>
            <p>{{ progress.current_rows_str }}</p>
          </div>
          <div class="metric-card">
            <span>Target per query</span>
            <p>{{ progress.target_per_query_str }}</p>
          </div>
          <div class="metric-card">
            <span>Partial CSV files</span>
            <p>{{ progress.partial_files }}</p>
          </div>
        </div>

        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-fill" id="progressFill" style="width: {{ progress.percent }}%"></div>
          </div>
          <div class="progress-text" id="progressText">{{ progress.message }}</div>
        </div>
        {% endif %}

        <p><strong>Log file:</strong> {{ log_file }}{% if log_link %} · <a href="{{ log_link }}">View recent log</a>{% endif %}</p>

        {% if log_preview %}
        <div class="log-section">
          <button class="log-toggle" onclick="toggleLog()">
            <span><i class="fa-solid fa-terminal"></i> Recent log output</span>
            <i class="fa-solid fa-chevron-down" id="logIcon"></i>
          </button>
          <div class="log-content" id="logContent">
            <pre>{{ log_preview }}</pre>
          </div>
        </div>
        {% endif %}

        <div style="margin-top: 24px;">
          <a class="button primary" href="{{ url_for('index') }}"><i class="fa-solid fa-arrow-left"></i> Back to Dashboard</a>
          {% if not error %}
          <button class="button" onclick="refreshPage()" style="margin-left: 12px;"><i class="fa-solid fa-refresh"></i> Refresh Status</button>
          {% endif %}
        </div>
      </div>
    </div>

    <script>
      let progressInterval;

      function toggleLog() {
        const content = document.getElementById('logContent');
        const icon = document.getElementById('logIcon');
        const isExpanded = content.classList.contains('expanded');

        if (isExpanded) {
          content.classList.remove('expanded');
          icon.classList.remove('fa-chevron-up');
          icon.classList.add('fa-chevron-down');
        } else {
          content.classList.add('expanded');
          icon.classList.remove('fa-chevron-down');
          icon.classList.add('fa-chevron-up');
        }
      }

      function refreshPage() {
        window.location.reload();
      }

      {% if not error %}
      // Auto-refresh every 10 seconds so metrics update with new CSV output.
      setTimeout(() => {
        refreshPage();
      }, 10000);
      {% endif %}
    </script>
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
    start_date: str = "",
    end_date: str = "",
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
        if keyword or start_date or end_date:
            query_text = keyword.strip() or '("Kemenlu" OR "@menluRI")'
            if start_date or end_date:
                start = start_date or end_date
                end = end_date or start_date
                query_text = f"{query_text} since:{start} until:{end}"
            if "lang:" not in query_text:
                query_text = f"{query_text} lang:id"
            env["SEARCH_QUERIES"] = query_text
        if output_dir:
            env["OUTPUT_DIR"] = output_dir.strip()
        if gdrive_dir:
            env["GDRIVE_DIR"] = gdrive_dir.strip()
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


def get_csv_row_count(csv_path: Path) -> int:
    try:
        with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
            return max(sum(1 for _ in f) - 1, 0)
    except Exception:
        return 0


def get_crawl_progress(target: str, output_dir: str, tweet_limit: str) -> dict:
    if target != "tweets":
        return {
            "current_rows": 0,
            "current_rows_str": "0",
            "target_per_query": 0,
            "target_per_query_str": "0",
            "partial_files": 0,
            "percent": 0,
            "message": "Progress metrics are only available for tweet crawls.",
        }

    path = BASE_DIR / (output_dir.strip() or "tweets-data")
    csv_paths = sorted(path.glob("*.csv")) if path.exists() else []
    current_rows = sum(get_csv_row_count(csv_path) for csv_path in csv_paths)
    target_per_query = int(tweet_limit) if tweet_limit.isdigit() and int(tweet_limit) > 0 else DEFAULT_LIMIT
    percent = min(100, int((current_rows / target_per_query) * 100)) if target_per_query else 0
    message = (
        f"Telah mengumpulkan {current_rows:,} tweet dari target per query {target_per_query:,}."
        if current_rows > 0
        else "Belum ada file CSV partial yang terdeteksi. Silakan refresh setelah proses berjalan beberapa detik."
    )

    return {
        "current_rows": current_rows,
        "current_rows_str": f"{current_rows:,}",
        "target_per_query": target_per_query,
        "target_per_query_str": f"{target_per_query:,}",
        "partial_files": len(csv_paths),
        "percent": percent,
        "message": message,
    }


def resolve_csv_path(directory: str, filename: str) -> Path:
    if directory not in DATA_DIRS:
        raise FileNotFoundError("Directory not permitted.")
    target_dir = DATA_DIRS[directory]
    target_path = (target_dir / filename).resolve()
    if not target_path.exists() or target_path.parent != target_dir.resolve():
        raise FileNotFoundError("File not found.")
    return target_path


def read_last_lines(file_path: Path, line_count: int = 20) -> str:
    try:
        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            return "".join(deque(f, maxlen=line_count))
    except Exception:
        return ""


@app.route("/")
def index() -> str:
    files_by_dir = list_csv_files()
    summary = build_dashboard_summary(files_by_dir)

    preview_directory = request.args.get("preview_directory", "").strip()
    preview_filename = request.args.get("preview_filename", "").strip()
    preview = None

    if preview_directory and preview_filename:
        try:
            csv_path = resolve_csv_path(preview_directory, preview_filename)
            df_preview = pd.read_csv(csv_path, dtype=str, nrows=20)
            row_count, column_count = get_csv_metadata(csv_path)
            preview = {
                "filename": preview_filename,
                "directory": preview_directory,
                "row_count": row_count,
                "column_count": column_count,
                "columns": df_preview.columns.tolist(),
                "rows": df_preview.fillna("").values.tolist(),
            }
        except Exception:
            preview = {"filename": preview_filename, "directory": preview_directory, "columns": [], "rows": []}

    return render_template_string(
        INDEX_PAGE,
        files_by_dir=files_by_dir,
        summary=summary,
        preview=preview,
    )


@app.route("/crawl/<target>")
def crawl_target(target: str) -> str:
    keyword = request.args.get("keyword", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    input_csv = request.args.get("input_csv", "").strip()
    max_threads = request.args.get("max_threads", "").strip()
    tweet_limit = request.args.get("tweet_limit", "").strip()
    output_dir = request.args.get("output_dir", "").strip()
    gdrive_dir = request.args.get("gdrive_dir", "").strip()

    try:
        script_name, log_file, started = start_crawl(
            target,
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
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
        if target == "tweets" and start_date and end_date:
            message += f" Range: {start_date}–{end_date}."
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

    log_link = None
    log_preview = ""
    if not error and log_file != "n/a":
        log_link = url_for("view_crawl_log", target=target)
        log_path = CRAWL_LOG_DIR / f"{target}_crawl.log"
        log_preview = read_last_lines(log_path, line_count=20)

    progress = get_crawl_progress(target, output_dir, tweet_limit)

    return render_template_string(
        CRAWL_PAGE,
        target_name=target.replace("_", " ").title(),
        status=status,
        message=message,
        log_file=log_file,
        log_link=log_link,
        log_preview=log_preview,
        error=error,
        script_name=script_name if 'script_name' in locals() else CRAWL_SCRIPTS.get(target, ""),
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        input_csv=input_csv,
        started=started if 'started' in locals() else False,
        progress=progress,
    )


@app.route("/download")
def download_file() -> object:
    directory = request.args.get("directory", "")
    filename = request.args.get("filename", "")
    if not filename:
        return redirect(url_for("index"))
    try:
        csv_path = resolve_csv_path(directory, filename)
    except FileNotFoundError:
        abort(404)

    return send_file(
        str(csv_path),
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/crawl-log/<target>")
def view_crawl_log(target: str) -> str:
    log_path = CRAWL_LOG_DIR / f"{target}_crawl.log"
    if not log_path.exists():
        return render_template_string(
            CRAWL_PAGE,
            target_name=target.replace("_", " ").title(),
            status="Log not available.",
            message="No log file exists yet.",
            log_file="n/a",
            log_link=None,
            log_preview="",
            error=True,
            script_name=CRAWL_SCRIPTS.get(target, ""),
            keyword="",
            start_date="",
            end_date="",
            input_csv="",
            started=False,
        )
    return render_template_string(
        CRAWL_PAGE,
        target_name=target.replace("_", " ").title(),
        status="Showing recent log.",
        message=f"Displaying the latest log entries for {target}.",
        log_file=log_path.name,
        log_link=None,
        log_preview=read_last_lines(log_path, line_count=100),
        error=False,
        script_name=CRAWL_SCRIPTS.get(target, ""),
        keyword="",
        start_date="",
        end_date="",
        input_csv="",
        started=False,
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
