#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

output="$({ yt-dlp -v --simulate "https://example.com/" 2>&1 || true; })"

if echo "$output" | grep -qF "Plugin directories: none"; then
  echo "FAIL: yt-dlp did not load any plugin directory." >&2
  echo "Use: yt-dlp-ps  OR  python3 -m yt_dlp  OR  scripts/yt-dlp-with-plugin.sh" >&2
  echo "Bare 'yt-dlp' often uses a different Python than 'pip install -e .'." >&2
  exit 1
fi

if ! echo "$output" | grep -qF "Extractor Plugins"; then
  echo "FAIL: No Extractor Plugins line in yt-dlp verbose output." >&2
  exit 1
fi

if ! echo "$output" | grep -qF "PageStreamIE"; then
  echo "FAIL: PageStreamIE not listed in Extractor Plugins." >&2
  exit 1
fi

echo "$output" | grep -F "Extractor Plugins"
echo "OK: plugin loaded. For downloads use yt-dlp-ps (not bare yt-dlp unless same Python)."
