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
# Extra arguments are passed through to yt-dlp after the built-in referer headers.
set -euo pipefail

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
  yt-dlp \
    --referer "$referer" \
    --add-header "Origin:${origin}" \
    "$@" \
    "$url"
done < "$jsonl_file"
