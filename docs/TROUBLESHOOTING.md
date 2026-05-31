# Troubleshooting

Problem → cause → fix for **yt-dlp-page-stream**.

---

## HTTP 428 Precondition Required

**Symptom**

```text
ERROR: [generic] Unable to download webpage: HTTP Error 428: Precondition Required
```

or

```text
ERROR: [tokenized_cdn] ... HTTP 428: this CDN requires a Referer
```

**Cause**

The CDN expects a **Referer** (and often **Origin**) from the video page. yt-dlp’s generic extractor, or a bare CDN URL without `tokenized_cdn:referer`, does not send them.

**Fix — preferred**

Download from the **video page URL**:

```bash
page-stream-yt-dlp "https://yoursite.com/video/123/"
```

**Fix — CDN URL only**

Pass the page URL as referer:

```bash
page-stream-yt-dlp --extractor-args "tokenized_cdn:referer=https://yoursite.com/video/123/" \
  "https://cdn.example.com/file.mp4?token=TOKEN&expires=EXPIRES"
```

**Fix — batch JSONL**

Re-extract with headers included:

```bash
page-stream-extract -i urls.txt -o streams.jsonl --format jsonl
./scripts/download-jsonl.sh streams.jsonl
```

---

## Plugin not loaded (generic extractor)

**Symptom**

Verbose log shows `[generic]` instead of `[page_stream]` or `[tokenized_cdn]`:

```bash
yt-dlp -v --simulate "https://yoursite.com/video/123/" 2>&1 | head -20
```

No line like:

```text
[debug] Extractor Plugins: PageStreamIE, TokenizedCdnIE
```

Or debug shows:

```text
[debug] Plugin directories: none
```

**Symptom — verify passed, downloads still use generic**

`./scripts/verify-plugin.sh` prints `PageStreamIE`, but `yt-dlp -a urls.txt` from another folder still shows `[generic]`.

**Cause**

`verify-plugin.sh` sets `PYTHONPATH` for that check only. Bare **`yt-dlp`** on your PATH (often Homebrew) uses a **different Python** than `pip install -e .`, so the plugin is not loaded during real downloads.

**Fix**

After `pip install -e .` and `pip install yt-dlp` in the same environment:

```bash
page-stream-yt-dlp -a urls.txt
# or:
python3 -m yt_dlp -a urls.txt
```

If you keep Homebrew’s `yt-dlp`:

```bash
/path/to/yt-dlp-page-stream/scripts/yt-dlp-with-plugin.sh -a urls.txt
```

Confirm with:

```bash
page-stream-yt-dlp -v --simulate "https://yoursite.com/video/123/" 2>&1 | head -5
```

You should see `[page_stream]` (or a clear `page_stream` error), not `[generic]`.

Other options:

1. Reinstall in the same environment: `pip install -e /path/to/yt-dlp-page-stream`
2. Manual plugin tree under `~/.config/yt-dlp/plugins/` (see [README](../README.md#manual-plugin-directory))

---

## Homebrew yt-dlp has no pip

**Symptom**

`pip install -e .` installs for system Python, but `yt-dlp` from Homebrew still does not load the plugin.

**Cause**

There is no Homebrew formula for **yt-dlp-page-stream**—only for yt-dlp. Homebrew’s `yt-dlp` bundles its own Python without pip, so a separate `pip install -e .` does not wire the plugin into that binary.

**Fix (pick one)**

**A — pipx yt-dlp (recommended)**

```bash
brew install pipx
pipx install "yt-dlp[default]"
pipx inject yt-dlp /path/to/yt-dlp-page-stream
```

**B — PYTHONPATH**

```bash
export PYTHONPATH="/path/to/yt-dlp-page-stream:${PYTHONPATH}"
```

Add that line to your shell profile if you use it often.

---

## Extraction failed / no formats

**Symptom**

```text
ERROR: [page_stream] ... No supported video embed or stream URL found on this page
```

or CLI prints `Failed to extract.`

**Cause**

The page does not contain a supported iframe pattern, or the player markup changed.

**Fix**

1. Open the page in a browser → View Source or DevTools → search for:

   - `snstr.php?fileid=`
   - `snstrhls.php?fileid=`

2. If neither appears, this site is not supported yet.

3. If the iframe exists but extraction still fails, the player HTML may use a format the regex does not match — open an issue with a **non-piracy** example URL if you can share one.

---

## Expired token on CDN URL

**Symptom**

Download worked before; now 403, 428, or empty file. URL contains `token=` and `expires=`.

**Cause**

Signed CDN URLs are time-limited.

**Fix**

Do not reuse old lines from `streams.txt`. Re-extract from the page:

```bash
page-stream-extract -i urls.txt -o streams.jsonl --format jsonl --keep-input
```

Then download again with `download-jsonl.sh` or `yt-dlp` on the page URL.

---

## SSL / certificate errors

**Symptom**

Certificate verify failed when fetching the page (outside yt-dlp).

**Note**

The shared extractor in [`extractor/core.py`](../extractor/core.py) disables SSL verification for page/iframe fetches. If errors persist:

- Check VPN, proxy, or corporate TLS inspection.
- Confirm the page loads in a normal browser on the same network.

---

## Still stuck?

1. Run with verbose logging and save the log:

   ```bash
   yt-dlp -v "https://yoursite.com/video/123/" 2>&1 | tee yt-dlp-debug.log
   ```

2. Open an issue at [github.com/hamza-siddiq/yt-dlp-page-stream/issues](https://github.com/hamza-siddiq/yt-dlp-page-stream/issues) with the log and a description of the page type (no copyrighted content required in the report if you prefer).
