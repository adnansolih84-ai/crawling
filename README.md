# glowing-giggle
Dashboard untuk melakukan crawling di media sosial X.

## Ringkasan
`glowing-giggle` adalah aplikasi Python sederhana untuk:
- menampilkan hasil crawling CSV di web dashboard
- crawling tweet/X dengan filter Bahasa Indonesia
- crawling komentar thread berdasarkan hasil tweet CSV

## Bab 1: Pendahuluan
Proyek ini dirancang untuk membantu peneliti dan analis data yang ingin mengumpulkan dan mengevaluasi data Twitter/X dalam konteks topik khusus.
Fokus utama adalah mengumpulkan tweet berbahasa Indonesia, melakukan filter, dan mengumpulkan komentar thread dari tweet penting.

## Bab 2: Arsitektur Sistem
Aplikasi ini terdiri dari tiga komponen utama:
1. `web_view.py` — dashboard web untuk menampilkan CSV hasil crawling, memicu crawling baru, dan mengelola dataset.
2. `twitter_crawler.py` — crawler tweet yang mengumpulkan data tweet menggunakan `tweet-harvest`, memfilter bahasa Indonesia, dan menyimpan CSV.
3. `twitter_thread_comments.py` — crawler komentar thread yang membaca file CSV tweet, menyortir URL thread, lalu mengumpulkan komentar setiap thread.

Folder output standar:
- `tweets-data/` untuk CSV tweet
- `thread-comments/` untuk CSV komentar thread
- `crawl-logs/` untuk log eksekusi crawler dari dashboard

## Bab 3: Instalasi dan Persiapan
1. Pastikan Python 3.11+ sudah terpasang.
2. Install paket Python dengan perintah:

```bash
python3 -m pip install -r requirements.txt
```

3. Pastikan `twitter_crawler.py` dan `twitter_thread_comments.py` tersedia di folder repository.
4. Untuk menjalankan crawler, siapkan token Twitter/X pada environment variable `TWITTER_AUTH_TOKEN`:

```bash
export TWITTER_AUTH_TOKEN="..."
```

5. Jika menggunakan Google Drive di environment seperti Colab atau Codespaces, pastikan path `GDRIVE_DIR` sudah benar.

## Menjalankan Dashboard
Untuk menampilkan dashboard dan melihat hasil CSV:

```bash
python3 web_view.py
```

Buka browser ke:

```
http://127.0.0.1:5000
```

## Bab 4: Dashboard Web
Dashboard `web_view.py` menampilkan ringkasan dataset dan preview CSV dari dua folder:
- `tweets-data/`
- `thread-comments/`

Fitur utama:
- ringkasan jumlah file CSV dan total baris
- daftar file tweet dan thread comment
- preview CSV langsung di browser
- form untuk memicu crawling tweet
- form untuk memicu crawling komentar thread

### Cara menggunakan
1. Letakkan file CSV hasil crawling di folder `tweets-data/` atau `thread-comments/`.
2. Buka `http://127.0.0.1:5000`.
3. Tekan tombol `Refresh` untuk memuat ulang daftar file.
4. Klik `View` untuk melihat preview file.
5. Gunakan form `Keyword pencarian` dan `Tahun mulai`/`Tahun selesai` untuk memulai crawl tweet baru.
6. Gunakan form `Crawl thread comments` untuk memulai crawl komentar dari file CSV yang berisi kolom `tweet_url`.

## Bab 5: Crawling Tweet
File crawler untuk tweet adalah `twitter_crawler.py`.

### Tujuan
Crawler ini menjalankan `tweet-harvest` untuk mengumpulkan tweet berdasarkan keyword dan rentang tanggal, lalu:
- menyimpan hasil ke folder `tweets-data/`
- memfilter tweet berbahasa Indonesia dengan `langdetect`
- menyimpan file hasil akhir berlabel `FULL_ID`
- mendukung salinan ke Google Drive dengan variabel `GDRIVE_DIR`

### Environment variables
- `TWITTER_AUTH_TOKEN` = token akses API Twitter/X
- `SEARCH_QUERIES` = query lengkap yang dipisah koma
- `SEARCH_KEYWORD` = kata kunci pencarian jika `SEARCH_QUERIES` tidak diset
- `START_DATE` = tanggal mulai (format YYYY-MM-DD)
- `END_DATE` = tanggal selesai (format YYYY-MM-DD)
- `START_YEAR` = tahun mulai (fallback kompatibilitas)
- `END_YEAR` = tahun selesai (fallback kompatibilitas)
- `OUTPUT_DIR` = folder keluaran CSV
- `GDRIVE_DIR` = folder Google Drive tujuan
- `TWEET_LIMIT` = batas tweet per query

### Contoh jalankan

```bash
export TWITTER_AUTH_TOKEN="..."
export SEARCH_KEYWORD='("Kemenlu" OR "@menluRI")'
export START_DATE=2024-01-01
export END_DATE=2025-12-31
python3 twitter_crawler.py
```

## Bab 6: Crawling Thread Comments
File crawler untuk komentar thread adalah `twitter_thread_comments.py`.

### Tujuan
Crawler ini membaca CSV tweet yang sudah ada, kemudian:
- menyortir tweet berdasarkan `retweet_count` atau `created_at`
- mengekstrak URL thread dari kolom `tweet_url`
- menjalankan `tweet-harvest --thread` untuk setiap URL
- menggabungkan hasil komentar thread menjadi satu CSV
- mendukung penyimpanan ke Google Drive dengan variabel `GDRIVE_DIR`

### Environment variables
- `TWITTER_AUTH_TOKEN` = token akses API Twitter/X
- `INPUT_CSV_PATH` = path file CSV input
- `OUTPUT_DIR` = folder keluaran CSV thread comment
- `GDRIVE_DIR` = folder Google Drive tujuan
- `TWEET_LIMIT` = batas komentar per thread
- `MAX_THREADS` = batas maksimal thread yang akan dicrawl (0 = semua)

### Contoh jalankan

```bash
export TWITTER_AUTH_TOKEN="..."
export INPUT_CSV_PATH="tweets-data/KemenluDynamicStance_PART1.csv"
export OUTPUT_DIR="thread-comments"
export MAX_THREADS=20
python3 twitter_thread_comments.py
```

### Notes
- Pastikan CSV input memiliki kolom `tweet_url`.
- Jika tidak ditemukan kolom `retweet_count`, crawler akan fallback ke `created_at`.
- Hasil akhir akan disimpan di `thread-comments/` dan dapat disalin ke Google Drive jika `GDRIVE_DIR` diset.
