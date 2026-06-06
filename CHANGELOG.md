# Changelog

All notable changes to **yt-dlp-page-stream** are documented here.

## [Unreleased]

### Added

- **`yt-dlp-ps --clipboard`** — batch-download page URLs copied to the system clipboard (one per line) instead of using `-a urls.txt`

### Documentation

- `yt-dlp-ps` is the primary download command; `yt-dlp-page-stream` is a supported alias (same entry point). Only `page-stream-yt-dlp` is deprecated.
- Discoverability: [docs/DISCOVERABILITY.md](docs/DISCOVERABILITY.md); upstream wiki listing requested in [yt-dlp#16846](https://github.com/yt-dlp/yt-dlp/issues/16846)

## [2.2.5] - 2026-05-31

### Documentation

- README and package description clarify that the project extends yt-dlp; `yt-dlp-ps` runs full yt-dlp with the plugin
- README **Uninstall** section (pip, pipx, manual plugin path; no custom CLI command)
- CONTRIBUTING / EXAMPLES wording; TROUBLESHOOTING links to uninstall

## [2.2.4] - 2026-05-31

### Fixed

- **`--update` upgrade** runs `git pull` and `pip install -e` in the **package clone** (absolute path), not your current shell directory
- Auto-runs `git pull` before reinstall; no longer prints a misleading “run git pull first” then fails
- Reports failed steps instead of **Upgrade complete.** when pip did not change versions

## [2.2.3] - 2026-05-31

### Fixed

- **`--update`** no longer claims updates are available when PyPI/GitHub could not be reached (`latest: unknown`)
- HTTPS checks use **certifi** CA bundle (common macOS Python SSL fix); longer timeout
- Cached last-known remote versions shown when a check fails mid-flight
- Plugin latest version read from **main** `pyproject.toml` when the repo has no GitHub releases/tags

## [2.2.2] - 2026-05-31

### Changed

- **`--update`** always shows installed vs latest remote versions
- Detects upgrades done outside `--update` (e.g. `git pull`) via cached versions: **updated since last check**
- After pip upgrades: **Upgrade complete.** with **before → after** version lines

## [2.2.1] - 2026-05-31

### Added

- **`yt-dlp-ps --version`** / **`-V`** — print installed `yt-dlp-page-stream` and `yt-dlp` versions

### Changed

- **`--update`** shows a spinner while checking remotes; pip upgrades run under a status spinner with **Upgrade finished.** when done
- **All up to date.** also lists installed versions

## [2.2.0] - 2026-05-31

### Added

- **Rich** terminal UX: progress bar for `page-stream-extract`; panels and confirm for `yt-dlp-ps --update`
- [`cli_ui.py`](cli_ui.py) helpers with plain-text fallback when not a TTY

### Note

- Download progress remains **yt-dlp’s native bar**; Rich is not used during `yt-dlp-ps` downloads

## [2.1.4] - 2026-05-31

### Fixed

- **page_stream** no longer blocks other sites: `suitable()` requires a snstr embed; otherwise yt-dlp uses built-in extractors (YouTube, etc.)
- If extraction fails after a positive `suitable()` check, raise `ExtractorError(expected=True)` so yt-dlp can fall back

## [2.1.3] - 2026-05-31

### Added

- **`yt-dlp-ps --update`** — force version check (bypass 24h cache), prompt to upgrade yt-dlp and this plugin via pip

### Changed

- Entry module renamed `page_stream_yt_dlp.py` → `yt_dlp_page_stream.py`

## [2.1.2] - 2026-05-31

### Added

- **`yt-dlp-ps`** — short download command (page stream)

### Changed

- Primary CLI is now `yt-dlp-ps`; `yt-dlp-page-stream` and `page-stream-yt-dlp` remain as aliases

## [2.1.1] - 2026-05-31

### Fixed

- Clearer error when a batch URL is a listing page (e.g. `/page/3/`) instead of a video page
- Duplicate `http_headers` on info dict so yt-dlp always sends Referer/Origin on CDN downloads

## [2.1.0] - 2026-05-31

### Added

- `yt-dlp` as a required pip dependency — `pip install -e .` installs plugin and yt-dlp together
- **`yt-dlp-page-stream`** console script (download command matches package / plugin name)
- Pre-run update notifications (interactive TTY, 24h cache): outdated **yt-dlp** on PyPI and plugin on GitHub

### Changed

- **`page-stream-yt-dlp`** is a deprecated alias for `yt-dlp-page-stream` (removed in a future release)
- README / docs: one-step install; use `yt-dlp-page-stream` instead of bare `yt-dlp` in examples

### Environment

- `YT_DLP_PAGE_STREAM_SKIP_UPDATE_CHECK=1` — disable update checks
- `YT_DLP_PAGE_STREAM_UPDATE_PROMPT=1` — optional `pip` upgrade prompt when updates are found

## [2.0.3] - 2026-05-31

### Fixed

- `page-stream-yt-dlp` console script now loads plugins reliably (setuptools puts `bin/` on `sys.path`, which hid `yt_dlp_plugins/`)

## [2.0.2] - 2026-05-31

### Added

- `page-stream-yt-dlp` console script — runs yt-dlp in the same Python as `pip install -e .` (plugin always loaded)
- `scripts/yt-dlp-with-plugin.sh` — Homebrew `yt-dlp` wrapper with repo on `PYTHONPATH`

### Changed

- `page_stream` suitability is regex-only; embed detection runs in `_real_extract` (avoids silent fallback to generic)
- `scripts/verify-plugin.sh` fails on `Plugin directories: none` and prints download command hints
- README / troubleshooting: use `page-stream-yt-dlp` for downloads, not bare `yt-dlp` when Pythons differ

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
