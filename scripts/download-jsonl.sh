#!/usr/bin/env bash
# Download media from JSONL produced by:
#   page-stream-extract -i urls.txt -o streams.jsonl --format jsonl
#
# JSONL schema (one JSON object per line):
#   url      - direct m3u8 or mp4 URL
#   referer  - video page URL (sent as Referer header)
#   origin   - page origin, e.g. https://yoursite.com (sent as Origin header)
#   page     - same as referer (not read by this script)
#   user_agent - optional (not read; yt-dlp uses its own UA unless you pass flags)
#
# Usage:
#   ./scripts/download-jsonl.sh streams.jsonl
#   ./scripts/download-jsonl.sh streams.jsonl -o "%(id)s.%(ext)s" -f best
#
# Extra arguments are passed through to yt-dlp-ps after the built-in referer headers.
set -euo pipefail

YTDLP_CMD="yt-dlp-ps"
if ! command -v "$YTDLP_CMD" >/dev/null 2>&1; then
  if command -v yt-dlp-page-stream >/dev/null 2>&1; then
    YTDLP_CMD="yt-dlp-page-stream"
  elif command -v page-stream-yt-dlp >/dev/null 2>&1; then
    YTDLP_CMD="page-stream-yt-dlp"
  else
    echo "Install the plugin first: pip install -e .  (provides yt-dlp-ps)" >&2
    exit 1
  fi
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 streams.jsonl [extra yt-dlp args...]" >&2
  exit 1
fi

jsonl_file="$1"
shift

if [[ ! -f "$jsonl_file" ]]; then
  echo "File not found: $jsonl_file" >&2
  exit 1
fi

while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" ]] && continue
  url=$(printf '%s' "$line" | python3 -c 'import json,sys; print(json.load(sys.stdin)["url"])')
  referer=$(printf '%s' "$line" | python3 -c 'import json,sys; print(json.load(sys.stdin)["referer"])')
  origin=$(printf '%s' "$line" | python3 -c 'import json,sys; print(json.load(sys.stdin)["origin"])')
  echo "Downloading: $url"
  "$YTDLP_CMD" \
    --referer "$referer" \
    --add-header "Origin:${origin}" \
    "$@" \
    "$url"
done < "$jsonl_file"
