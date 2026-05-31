# Contributing

Thanks for helping improve **yt-dlp-page-stream**.

## Scope

This project is a **separate yt-dlp plugin package** plus a small stdlib CLI. **Not a fork** — downloads still use yt-dlp’s engine and flags; this repo only ships extra extractors and helpers. It is intentionally **not** merged into [yt-dlp](https://github.com/yt-dlp/yt-dlp) core: the extractor targets a cross-site embed pattern, uses broad URL matching, and is maintained here so changes do not depend on upstream release cycles.

## Development setup

This project is not on PyPI or Homebrew—use an editable install from a clone:

```bash
git clone https://github.com/hamza-siddiq/yt-dlp-page-stream.git
cd yt-dlp-page-stream
pip install -e .
```

Verify plugins load:

```bash
chmod +x scripts/verify-plugin.sh
./scripts/verify-plugin.sh
```

Expected: `PageStreamIE`, `TokenizedCdnIE`.

Or, after `pip install -e .` in the same Python as yt-dlp:

```bash
python3 -m yt_dlp -v --simulate "https://example.com/" 2>&1 | grep -F "Extractor Plugins"
```

Test extraction (no download):

```bash
yt-dlp-ps --simulate "https://yoursite.com/video/123/"
```

Test CLI:

```bash
page-stream-extract -i examples/urls.example.txt -o /tmp/streams.txt
```

## Pull requests

1. **Update docs** if behavior, flags, or extractor names change (`README.md`, `docs/`, `examples/`, `CHANGELOG.md`).
2. **Keep regex changes minimal** — only extend patterns when you have a real page sample.
3. **No support for sites primarily used for piracy** — maintainers may decline embed patterns whose only use is copyright infringement.
4. Prefer **readable names** in code (`page_stream`, not opaque abbreviations).

## Reporting bugs

Use [GitHub Issues](https://github.com/hamza-siddiq/yt-dlp-page-stream/issues). Include:

- yt-dlp version (`yt-dlp --version`)
- Whether `Extractor Plugins: PageStreamIE` appears in `yt-dlp -v` output
- The **type** of URL (page vs CDN), not necessarily the full URL if sensitive

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common fixes before filing.
