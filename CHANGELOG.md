# Changelog

All notable changes to **yt-dlp-page-stream** are documented here.

## [2.0.1] - 2026-05-31

### Added

- `scripts/verify-plugin.sh` — reliable plugin check via `PYTHONPATH` (works with Homebrew `yt-dlp`)

### Changed

- `tokenized_cdn` matches any host with signed query params (`token` / `expires`), not a single CDN domain
- Plugin verification docs use `./scripts/verify-plugin.sh` or `python3 -m yt_dlp` when `yt-dlp` uses a different Python
- setuptools namespace packaging for `yt_dlp_plugins` (yt-dlp sample-plugins pattern)
- Documentation and examples use placeholder hosts (`cdn.example.com`, `yoursite.com`)

## [2.0.0] - 2026-05-31

### Added

- yt-dlp plugin with extractors `page_stream` and `tokenized_cdn`
- `Referer` / `Origin` headers on formats to fix HTTP 428 on tokenized CDNs
- CLI `--format jsonl` output (`url`, `referer`, `origin`, `page`, `user_agent`)
- `scripts/download-jsonl.sh` for batch downloads from JSONL
- Entry point `page-stream-extract` (alias `convert-links`)

### Changed

- Repository renamed from `m3u8-link-extractor` to **yt-dlp-page-stream**
- Package name `yt-dlp-page-stream` in `pyproject.toml` (install via `pip install -e .` from git; not published to PyPI)
- Extractor `snstr` renamed to `page_stream` (only relevant if you used a pre-release checkout)
- Extractor `protectedcdn` renamed to `tokenized_cdn`
- `--extractor-args protectedcdn:referer=...` → `tokenized_cdn:referer=...`
- `--base-url` is optional (derived from each page URL)

### Removed

- Standalone extraction-only positioning; yt-dlp plugin is the primary workflow

## [1.0.0] - Initial

- `convert_links.py` CLI to extract m3u8/mp4 URLs from pages with `snstr.php` / `snstrhls.php` iframes
- Published as **m3u8-link-extractor**
