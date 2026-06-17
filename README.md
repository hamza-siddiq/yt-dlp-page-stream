# yt-dlp-page-stream

> **Extends [yt-dlp](https://github.com/yt-dlp/yt-dlp)** — not a fork. Installs as a [plugin](https://github.com/yt-dlp/yt-dlp#plugins). **`yt-dlp-ps`** runs full yt-dlp with this plugin (same flags and built-in sites; adds `page_stream` / `tokenized_cdn` for video pages and signed CDN URLs).

**Plugin for yt-dlp** — adds extractors for **HLS (`.m3u8`)** and **MP4** from **video page URLs**, with `Referer` / `Origin` so tokenized CDNs do not return HTTP 428. URLs without a supported embed use yt-dlp’s **built-in extractors** (YouTube, etc.) as usual.

- Repository: [github.com/hamza-siddiq/yt-dlp-page-stream](https://github.com/hamza-siddiq/yt-dlp-page-stream)
- Requires: Python 3.8+ ([yt-dlp](https://github.com/yt-dlp/yt-dlp) installed automatically with `pip install -e .`)
- Changelog: [CHANGELOG.md](CHANGELOG.md) (formerly **m3u8-link-extractor**)
- Find plugins: [yt-dlp-plugin topic](https://github.com/topics/yt-dlp-plugin) · Wiki listing requested: [yt-dlp#16846](https://github.com/yt-dlp/yt-dlp/issues/16846)

**Topics:** `yt-dlp`, `yt-dlp-plugin`, `m3u8`, `hls`, `page-stream`

---

## Quick start

```bash
git clone https://github.com/hamza-siddiq/yt-dlp-page-stream.git
cd yt-dlp-page-stream
pip install -e .
yt-dlp-ps "https://yoursite.com/video/123/"
```

All `yt-dlp` flags work (`-f`, `-o`, `-a`, `--simulate`, …).

**Package name:** `yt-dlp-page-stream` · **Primary command:** `yt-dlp-ps` (short for page stream). **Also works:** `yt-dlp-page-stream` (same binary, matches the package name). **Deprecated:** `page-stream-yt-dlp`. Use `yt-dlp-ps`, `yt-dlp-page-stream`, or `python3 -m yt_dlp` in the same env—not bare **`yt-dlp`** on your PATH unless it shares the same Python as `pip install -e .`. Homebrew-only setups are described under [Installation](#installation).

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

1. You pass a URL to **`yt-dlp-ps`** (or the CLI extracts stream URLs in batch).
2. If the page has a supported embed, the **page_stream** plugin resolves the stream and sets headers.
3. Otherwise, yt-dlp uses its **usual extractors** for that site.
4. Downloads use the correct **Referer** and **Origin** when page_stream handles the URL.

**Why HTTP 428 happens without this plugin:** feeding a bare CDN URL (e.g. `cdn.example.com/...`) to yt-dlp’s **generic** extractor sends no Referer; many CDNs respond with **428 Precondition Required**.

---

## Installation

### What is and is not packaged

| Install method | This plugin | yt-dlp |
|----------------|-------------|--------|
| `pip install -e .` from a **git clone** | Yes | Yes (declared dependency) |
| `pip install yt-dlp-page-stream` on PyPI | **Not available** (not published) | — |
| `brew install yt-dlp-page-stream` | **No formula** | — |
| `brew install yt-dlp` | No | Yes — yt-dlp only |

From a git clone, **`pip install -e .` installs both** this plugin and yt-dlp. Homebrew-only or manual plugin paths are alternatives when Python stacks differ.

### pip from a clone (recommended)

```bash
git clone https://github.com/hamza-siddiq/yt-dlp-page-stream.git
cd yt-dlp-page-stream
pip install -e .
```

`pip install -e .` registers the plugin, **`yt-dlp-ps`** and **`yt-dlp-page-stream`** (same yt-dlp + plugin; prefer `yt-dlp-ps`), and **`page-stream-extract`**. Downloads must use one of those commands or `python3 -m yt_dlp`—not bare `yt-dlp` when Homebrew uses a different Python.

The legacy command **`page-stream-yt-dlp`** still works but is deprecated.

### Verify the plugin loaded

```bash
chmod +x scripts/verify-plugin.sh
./scripts/verify-plugin.sh
```

Expected: `PageStreamIE`, `TokenizedCdnIE`, and `OK: plugin loaded`.

The script **fails** if `Plugin directories: none` (bare `yt-dlp` without the plugin). Plugin extractors may not appear in `yt-dlp --list-extractors`.

**Downloads after `pip install -e .`:**

```bash
yt-dlp-ps -a urls.txt
# or copy URLs to the clipboard (one per line), then:
yt-dlp-ps --clipboard
# same Python as pip:
python3 -m yt_dlp -a urls.txt
```

`--clipboard` reads page URLs from the system clipboard (macOS: `pbpaste`; Linux: `xclip` or `xsel`; Windows: PowerShell). It cannot be combined with `-a` or URL arguments on the command line.

**Homebrew `yt-dlp` from any directory:**

```bash
/path/to/yt-dlp-page-stream/scripts/yt-dlp-with-plugin.sh -a urls.txt
```

### Homebrew yt-dlp (macOS)

`brew install yt-dlp` does **not** install this plugin. Homebrew’s yt-dlp also uses a bundled Python that usually has **no pip**, so `pip install -e .` on system Python will not affect `brew`-installed `yt-dlp`.

Pick one approach:

**A — pipx (yt-dlp + plugin in one Python stack)**

```bash
brew install pipx
pipx install "yt-dlp[default]"
pipx inject yt-dlp /path/to/yt-dlp-page-stream
```

**B — Keep Homebrew yt-dlp, use the wrapper script**

```bash
brew install yt-dlp
/path/to/yt-dlp-page-stream/scripts/yt-dlp-with-plugin.sh -a urls.txt
```

Or `export PYTHONPATH="/path/to/yt-dlp-page-stream:${PYTHONPATH}"` and run `./scripts/verify-plugin.sh` to confirm.

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

### Uninstall

There is no custom uninstall command—use the steps that match how you installed.

**pip / editable clone** (removes `yt-dlp-ps`, `yt-dlp-page-stream`, `page-stream-extract`, and this package):

```bash
pip uninstall yt-dlp-page-stream
```

`pip install -e .` also installs **yt-dlp** in that Python environment. If you still need yt-dlp after uninstalling this plugin:

```bash
pip install yt-dlp
```

**pipx** (plugin injected into yt-dlp):

```bash
pipx uninject yt-dlp /path/to/yt-dlp-page-stream
```

Use the same path you passed to `pipx inject`. To remove the whole pipx yt-dlp app: `pipx uninstall yt-dlp`.

**Manual plugin directory:**

```bash
rm -rf "${HOME}/.config/yt-dlp/plugins/yt-dlp-page-stream"
```

Remove any `PYTHONPATH` entry that pointed at a clone. The git clone itself is not deleted by these steps.

**Optional cleanup:** `rm -rf ~/.cache/yt-dlp-page-stream` (update-check cache).

### Update notifications

When you run **`yt-dlp-ps`** in an interactive terminal, it may check once per 24 hours whether **yt-dlp** (PyPI) or this package (GitHub releases) has a newer version and print upgrade hints. Checks are skipped in CI, pipes, and non-TTY sessions.

**Force check and upgrade (interactive):**

```bash
yt-dlp-ps --version    # yt-dlp-page-stream and yt-dlp versions
yt-dlp-ps --update     # spinner while checking; spinner per pip step when upgrading
```

Shows what is outdated and asks **`Upgrade now? [y/N]`**. On **yes**, runs `pip install -U yt-dlp` and/or `pip install -e .` (for git clones, run **`git pull`** in the repo first). **All up to date with PyPI / GitHub.** lists installed vs latest versions. If you upgraded manually (`git pull`, `pip install -e .`), the next run shows **updated since last check**. After confirming an upgrade, you get **Upgrade complete.** with version changes. Use with downloads to check before a batch:

```bash
yt-dlp-ps --update --ignore-errors -a urls.txt
```

This is **not** the same as **`yt-dlp -U`**, which only updates yt-dlp itself.

In a terminal, `--update` uses **Rich** panels and a confirm prompt. Download jobs still use **yt-dlp’s own progress bar** (not replaced).

| Environment variable | Effect |
|---------------------|--------|
| `YT_DLP_PAGE_STREAM_SKIP_UPDATE_CHECK=1` | Never background-check |
| `YT_DLP_PAGE_STREAM_UPDATE_PROMPT=1` | Background check: ask before `pip` when updates are found |

---

## Workflows

| You have | What to run |
|----------|-------------|
| A **video page URL** | `yt-dlp-ps "https://yoursite.com/video/123/"` |
| **Batch page URLs** | `yt-dlp-ps -a urls.txt` |
| **URLs on the clipboard** (one per line) | `yt-dlp-ps --clipboard` |
| A **CDN URL only** (e.g. from an old export) | `yt-dlp-ps --extractor-args "tokenized_cdn:referer=..." "https://cdn.example.com/file.mp4?token=TOKEN"` |
| A **list of page URLs** (extract streams only) | `page-stream-extract -i urls.txt -o streams.txt` |
| **JSONL** with url + referer + origin | `./scripts/download-jsonl.sh streams.jsonl` |
| **Homebrew yt-dlp** + plugin | `./scripts/yt-dlp-with-plugin.sh -a urls.txt` |

More recipes: [docs/EXAMPLES.md](docs/EXAMPLES.md).

### Download from a page URL

```bash
yt-dlp-ps "https://yoursite.com/video/123/"
```

The `page_stream` extractor resolves the stream and attaches headers automatically.

### Download from a CDN URL only

```bash
yt-dlp-ps --extractor-args "tokenized_cdn:referer=https://yoursite.com/video/123/" \
  "https://cdn.example.com/file.mp4?token=TOKEN&expires=EXPIRES"
```

The referer must be the **original video page** where you found the embed.

---

## Extractor reference

| Extractor | When it runs | Required `--extractor-args` |
|-----------|----------------|-----------------------------|
| `page_stream` | Video page with direct media (no dedicated extractor matches); de-duplicates repeated sources into a playlist | none |
| `tokenized_cdn` | Direct `.mp4` / `.m3u8` URL with `token=` or `expires=` query params | `referer=https://yoursite.com/video/123/` |

Force a specific extractor if needed:

```bash
yt-dlp-ps --ies page_stream "https://yoursite.com/video/123/"
```

---

## CLI: extract stream URLs

Batch-extract direct stream URLs without downloading. In a terminal, **`page-stream-extract`** shows a **Rich** progress bar and per-URL status; output is plain text when piped or non-interactive.

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

`page_stream` runs on any video page that **no built-in yt-dlp extractor already handles** and that exposes direct media URLs in its HTML or player iframe:

- `<source src="….mp4">` / `<video src="….m3u8">` — including pages that embed the **same video twice** (e.g. a lightbox player and an inline player); these are **de-duplicated**, so each file downloads once
- `og:video` / `og:video:url` meta tags pointing at `.mp4` / `.m3u8`
- JWPlayer `file: "….mp4"` config
- player iframes that load `snstr.php?fileid=...` / `snstrhls.php?fileid=...` embed scripts (third-party PHP script names on the remote site)

When a page has several unique sources, `page_stream` returns them as a **playlist** with the correct `Referer`/`Origin` headers. URLs that a dedicated extractor (YouTube, Vimeo, …) recognizes are left to that extractor — only the **generic** fallback is replaced. Signed CDN URLs work via `tokenized_cdn` when you supply the page referer.

---

## Troubleshooting

| Symptom | Quick fix |
|---------|-------------|
| Same file downloaded **multiple times** (similar names) | Update — `page_stream` now de-duplicates pages that embed a video more than once. Use **`yt-dlp-ps`**, not bare **`yt-dlp`** (which falls back to the duplicating generic extractor) |
| HTTP **428** on download | Use a **page URL**, or pass `tokenized_cdn:referer=<page>` for CDN URLs |
| `[generic]` in verbose log | Use **`yt-dlp-ps`**, not bare **`yt-dlp`**; run `./scripts/verify-plugin.sh` |
| Verify passed but downloads use `[generic]` | Same issue — verify script sets `PYTHONPATH`; downloads need `yt-dlp-ps` / `yt-dlp-page-stream` or `scripts/yt-dlp-with-plugin.sh` |
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

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). This project **extends** yt-dlp as a plugin (not part of yt-dlp core).

---

## License

MIT — see [LICENSE](LICENSE).
