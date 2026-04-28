# glowing-giggle
Dashboard untuk melakukan crawling di media sosial X

## Scripts

- `twitter_crawler.py` – crawler tweet/X dan filter Bahasa Indonesia
- `twitter_thread_comments.py` – crawl komentar thread dari file CSV yang sudah berisi tweet URL
- `web_view.py` – web viewer sederhana untuk menampilkan CSV hasil crawling di browser

## Web Viewer

1. Install dependensi:

```bash
pip install -r requirements.txt
```

2. Jalankan web server:

```bash
python3 web_view.py
```

3. Buka browser ke:

```
http://127.0.0.1:5000
```

Web viewer akan menampilkan file CSV dari folder lokal:
- `tweets-data/`
- `thread-comments/`

Pastikan file hasil crawling sudah tersedia di salah satu folder tersebut sebelum membuka web viewer.
