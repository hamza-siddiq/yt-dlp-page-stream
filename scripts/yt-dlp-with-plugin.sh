#!/usr/bin/env bash
# Run Homebrew (or other) yt-dlp with this repo's plugin on PYTHONPATH.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
exec yt-dlp "$@"
