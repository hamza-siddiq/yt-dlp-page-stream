# Changelog

All notable changes to **yt-dlp-page-stream** are documented here.

## [2.0.0] - 2026-05-31

### Added

- yt-dlp plugin with extractors `page_stream` and `tokenized_cdn`
- `Referer` / `Origin` headers on formats to fix HTTP 428 on tokenized CDNs
- CLI `--format jsonl` output (`url`, `referer`, `origin`, `page`, `user_agent`)
- `scripts/download-jsonl.sh` for batch downloads from JSONL
- Entry point `page-stream-extract` (alias `convert-links`)

### Changed

- Repository renamed from `m3u8-link-extractor` to **yt-dlp-page-stream**
- Package name `yt-dlp-page-stream` in `pyproject.toml`
- Extractor `snstr` renamed to `page_stream`
- Extractor `protectedcdn` renamed to `tokenized_cdn`
- `--base-url` is optional (derived from each page URL)

### Removed

- Standalone extraction-only positioning; yt-dlp plugin is the primary workflow

## [1.0.0] - Initial

- `convert_links.py` CLI to extract m3u8/mp4 URLs from pages with `snstr.php` / `snstrhls.php` iframes
- Published as **m3u8-link-extractor**
