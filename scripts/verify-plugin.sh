#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
{ yt-dlp -v --simulate "https://example.com/" 2>&1 || true; } | grep -F "Extractor Plugins"
