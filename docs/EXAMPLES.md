# Examples

Recipes use **`yt-dlp-ps`** (yt-dlp with this plugin). Copy-paste examples for **yt-dlp-page-stream** below.

---

## Single download from a page URL

```bash
yt-dlp-ps -o "%(title)s.%(ext)s" "https://yoursite.com/video/123/"
```

Pick a format:

```bash
yt-dlp-ps -f best "https://yoursite.com/video/123/"
```

---

## Single download from a CDN URL

When you only have the direct link:

```bash
yt-dlp-ps --extractor-args "tokenized_cdn:referer=https://yoursite.com/video/123/" \
  -o "video.%(ext)s" \
  "https://cdn.example.com/file.mp4?token=TOKEN&expires=EXPIRES"
```

---

## Batch extract stream URLs (text)

**urls.txt** — one page URL per line:

```text
https://yoursite.com/video/101/
https://yoursite.com/video/102/
```

Extract:

```bash
page-stream-extract -i urls.txt -o streams.txt
```

`streams.txt` will contain one direct media URL per line (appended on each run).

---

## Batch extract + download with yt-dlp

Extract URLs, then download each (generic yt-dlp; headers may be missing for some CDNs — prefer page URLs or JSONL):

```bash
page-stream-extract -i urls.txt -o streams.txt
yt-dlp-ps -a streams.txt
```

**Recommended:** download from page URLs so `page_stream` sets headers:

```bash
yt-dlp-ps -a urls.txt
```

(Requires `urls.txt` to contain page URLs, not CDN URLs.)

---

## Batch extract as JSONL

```bash
page-stream-extract -i urls.txt -o streams.jsonl --format jsonl
```

Download each entry with correct Referer and Origin:

```bash
./scripts/download-jsonl.sh streams.jsonl
```

Pass extra yt-dlp options after the file name:

```bash
./scripts/download-jsonl.sh streams.jsonl -o "%(id)s.%(ext)s" -f best
```

---

## Batch download page URLs (shell loop)

See [examples/urls-to-download.sh.example](../examples/urls-to-download.sh.example).

```bash
chmod +x urls-to-download.sh
./urls-to-download.sh urls.txt
```

---

## ffmpeg (direct MP4, JSONL line)

For a single MP4 URL when you already have a JSONL line with `referer` and `origin`:

```bash
URL="https://cdn.example.com/file.mp4?token=TOKEN"
REFERER="https://yoursite.com/video/123/"
ORIGIN="https://yoursite.com"

ffmpeg -headers "Referer: ${REFERER}\r\nOrigin: ${ORIGIN}\r\n" \
  -i "${URL}" -c copy -movflags +faststart output.mp4
```

For HLS (`.m3u8`), ffmpeg needs the same headers:

```bash
ffmpeg -headers "Referer: ${REFERER}\r\nOrigin: ${ORIGIN}\r\n" \
  -i "https://cdn.example.com/playlist.m3u8" -c copy output.mp4
```

---

## Keep input URLs after extraction

```bash
page-stream-extract -i urls.txt -o streams.jsonl --format jsonl --keep-input
```

Useful when appending to an output file across multiple runs.

---

## Force the page_stream extractor

```bash
yt-dlp-ps --ies page_stream "https://yoursite.com/video/123/"
```

Exclude generic if another extractor conflicts:

```bash
yt-dlp-ps --ies "page_stream,-generic" "https://yoursite.com/video/123/"
```
