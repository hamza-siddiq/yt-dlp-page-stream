# yt-dlp-page-stream

**yt-dlp plugin** — extract and download **HLS (`.m3u8`)** and **MP4** streams from **video page URLs**, with `Referer` / `Origin` headers so tokenized CDNs do not return HTTP 428.

- Repository: [github.com/hamza-siddiq/yt-dlp-page-stream](https://github.com/hamza-siddiq/yt-dlp-page-stream)
- Requires: [yt-dlp](https://github.com/yt-dlp/yt-dlp) (install separately), Python 3.8+
- Changelog: [CHANGELOG.md](CHANGELOG.md) (formerly **m3u8-link-extractor**)

**Suggested GitHub topics:** `yt-dlp`, `yt-dlp-plugin`, `m3u8`, `hls`, `page-stream`

---

## Quick start

```bash
git clone https://github.com/hamza-siddiq/yt-dlp-page-stream.git
cd yt-dlp-page-stream
pip install yt-dlp
pip install -e .
yt-dlp "https://yoursite.com/video/123/"
```

If you already have `yt-dlp` in the same Python environment, skip `pip install yt-dlp`. Homebrew-only setups are described under [Installation](#installation).

Use the **page URL** you open in a browser—not the raw CDN link.

---

## How it works

```mermaid
flowchart LR
  PageURL[Video page URL] --> FetchPage[Fetch page HTML]
  FetchPage --> Iframe[Load player iframe]
  Iframe --> StreamURL[Find m3u8 or mp4 URL]
  StreamURL --> Download[yt-dlp download with Referer and Origin]
```

1. You pass a **video page URL** to yt-dlp (or the CLI extracts stream URLs in batch).
2. The plugin finds the embedded player and the direct **stream URL**.
3. yt-dlp downloads with the same **Referer** and **Origin** the browser would send.

**Why HTTP 428 happens without this plugin:** feeding a bare CDN URL (e.g. `cdn.example.com/...`) to yt-dlp’s **generic** extractor sends no Referer; many CDNs respond with **428 Precondition Required**.

---

## Installation

### What is and is not packaged

| Install method | This plugin | yt-dlp |
|----------------|-------------|--------|
| `pip install -e .` from a **git clone** | Yes | No — install yt-dlp yourself |
| `pip install yt-dlp-page-stream` on PyPI | **Not available** (not published) | — |
| `brew install yt-dlp-page-stream` | **No formula** | — |
| `brew install yt-dlp` | No | Yes — yt-dlp only |

You always install **two pieces**: yt-dlp, then this plugin (clone + editable pip, `PYTHONPATH`, or manual plugin directory).

### pip from a clone (recommended)

```bash
git clone https://github.com/hamza-siddiq/yt-dlp-page-stream.git
cd yt-dlp-page-stream
pip install yt-dlp
pip install -e .
```

`pip install -e .` registers the plugin and CLI (`page-stream-extract`). It must run in the **same Python environment** as the `yt-dlp` you invoke—check with `which yt-dlp` and `which python3`.

### Verify the plugin loaded

```bash
yt-dlp -v --simulate "https://cdn.example.com/example.mp4" 2>&1 | grep "Extractor Plugins"
```

Expected output includes: `PageStreamIE`, `TokenizedCdnIE`.

Plugin extractors may not appear in `yt-dlp --list-extractors`; use the command above.

### Homebrew yt-dlp (macOS)

`brew install yt-dlp` does **not** install this plugin. Homebrew’s yt-dlp also uses a bundled Python that usually has **no pip**, so `pip install -e .` on system Python will not affect `brew`-installed `yt-dlp`.

Pick one approach:

**A — pipx (yt-dlp + plugin in one Python stack)**

```bash
brew install pipx
pipx install "yt-dlp[default]"
pipx inject yt-dlp /path/to/yt-dlp-page-stream
```

**B — Keep Homebrew yt-dlp, add plugin via PYTHONPATH**

```bash
brew install yt-dlp
export PYTHONPATH="/path/to/yt-dlp-page-stream:${PYTHONPATH}"
```

Run the verify command after either setup.

### Manual plugin directory

```bash
PLUGIN_DIR="${HOME}/.config/yt-dlp/plugins/yt-dlp-page-stream"
mkdir -p "${PLUGIN_DIR}"
cp -R yt_dlp_plugins extractor "${PLUGIN_DIR}/"
export PYTHONPATH="${PLUGIN_DIR}:${PYTHONPATH}"
```

Expected layout:

```
~/.config/yt-dlp/plugins/yt-dlp-page-stream/
├── extractor/
│   ├── __init__.py
│   └── core.py
└── yt_dlp_plugins/
    └── extractor/
        └── page_stream.py
```

See also: [yt-dlp plugin documentation](https://github.com/yt-dlp/yt-dlp#plugins).

---

## Workflows

| You have | What to run |
|----------|-------------|
| A **video page URL** | `yt-dlp "https://yoursite.com/video/123/"` |
| A **CDN URL only** (e.g. from an old export) | `yt-dlp --extractor-args "tokenized_cdn:referer=https://yoursite.com/video/123/" "https://cdn.example.com/file.mp4?token=TOKEN"` |
| A **list of page URLs** (extract streams) | `page-stream-extract -i urls.txt -o streams.txt` |
| **JSONL** with url + referer + origin | `./scripts/download-jsonl.sh streams.jsonl` |

More recipes: [docs/EXAMPLES.md](docs/EXAMPLES.md).

### Download from a page URL

```bash
yt-dlp "https://yoursite.com/video/123/"
```

The `page_stream` extractor resolves the stream and attaches headers automatically.

### Download from a CDN URL only

```bash
yt-dlp --extractor-args "tokenized_cdn:referer=https://yoursite.com/video/123/" \
  "https://cdn.example.com/file.mp4?token=TOKEN&expires=EXPIRES"
```

The referer must be the **original video page** where you found the embed.

---

## Extractor reference

| Extractor | When it runs | Required `--extractor-args` |
|-----------|----------------|-----------------------------|
| `page_stream` | URL is a video page with a supported player iframe | none |
| `tokenized_cdn` | URL matches `https://cdn.example.com/….mp4` or `.m3u8` | `referer=https://yoursite.com/video/123/` |

Force a specific extractor if needed:

```bash
yt-dlp --ies page_stream "https://yoursite.com/video/123/"
```

---

## CLI: extract stream URLs

Batch-extract direct stream URLs without downloading (stdlib only):

```bash
page-stream-extract -i urls.txt -o streams.txt
```

Equivalent:

```bash
python3 convert_links.py -i urls.txt -o streams.txt
```

### Options

| Flag | Description |
|------|-------------|
| `-i`, `--input` | **Required.** File with video page URLs, one per line |
| `-o`, `--output` | **Required.** File to **append** extracted stream URLs to |
| `-b`, `--base-url` | Site origin for relative iframe paths (optional; derived from each URL) |
| `--format` | `text` (default): one media URL per line. `jsonl`: one JSON object per line (see below) |
| `--keep-input` | Do not clear the input file after a successful run |

**Behavior:** On success, results are **appended** to the output file. The input file is **cleared** unless you pass `--keep-input`.

### JSONL output

```bash
page-stream-extract -i urls.txt -o streams.jsonl --format jsonl
./scripts/download-jsonl.sh streams.jsonl
```

Each line is a JSON object:

| Field | Description |
|-------|-------------|
| `url` | Direct m3u8 or mp4 URL |
| `referer` | Video page URL (for CDN requests) |
| `origin` | Page origin, e.g. `https://yoursite.com` |
| `page` | Same as `referer` |
| `user_agent` | Browser User-Agent used during extraction |

Example line: [examples/streams.jsonl.example](examples/streams.jsonl.example).

### Input format

One video page URL per line (not the raw CDN link). Blank lines are ignored. Lines starting with `#` are **not** ignored—use a comments-free file or strip them before running. See [examples/urls.example.txt](examples/urls.example.txt).

---

## Supported sites

Works on video pages whose player iframe loads embed scripts such as:

- `snstr.php?fileid=...`
- `snstrhls.php?fileid=...`

These are **third-party PHP script names on the remote site**, not a product this project is named after. Tokenized hosts like `cdn.example.com` work via `tokenized_cdn` when you supply the page referer.

---

## Troubleshooting

| Symptom | Quick fix |
|---------|-------------|
| HTTP **428** on download | Use a **page URL**, or pass `tokenized_cdn:referer=<page>` for CDN URLs |
| `[generic]` in verbose log | Plugin not loaded — reinstall or set `PYTHONPATH` |
| No formats / extraction failed | Page may not use a supported iframe — see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| Token expired | Re-run extraction from the page URL |

Full guide: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

---

## Limitations

- Only supports the embed / player markup this tool was built for; sites can change HTML without notice.
- SSL certificate verification is **disabled** in the extractor to tolerate invalid certs on some hosts.
- Use only on content you are **authorized** to access.

---

## Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). This project is maintained as a **yt-dlp plugin**, not as part of yt-dlp core.

---

## License

MIT — see [LICENSE](LICENSE).
