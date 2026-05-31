#!/usr/bin/env python3
import argparse
import json
import os

from extractor.core import extract_media_url


def main():
    parser = argparse.ArgumentParser(
        description="Extract HLS/MP4 stream URLs from video page URLs (for yt-dlp-page-stream)."
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Input file containing URLs (one per line)"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Output file to append extracted media links"
    )
    parser.add_argument(
        "-b",
        "--base-url",
        help="Base URL for relative iframe sources (default: derived from each page URL)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "jsonl"],
        default="text",
        help="Output format: plain URLs (text) or JSON lines with referer/origin (jsonl)",
    )
    parser.add_argument(
        "--keep-input",
        action="store_true",
        help="Do not clear the input file after processing",
    )
    args = parser.parse_args()

    input_file = args.input
    output_file = args.output

    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' does not exist.")
        return

    with open(input_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        print(f"No URLs found in {input_file}.")
        return

    print(f"Found {len(urls)} URLs in {input_file}. Converting...")

    results = []
    for i, url in enumerate(urls, 1):
        print(f"Processing {i}/{len(urls)}: {url}")
        extracted = extract_media_url(url, args.base_url)
        if extracted:
            results.append(extracted)
            print(f" -> Found: {extracted['url']}")
        else:
            print(" -> Failed to extract.")

    if results:
        with open(output_file, "a") as f:
            for item in results:
                if args.format == "jsonl":
                    f.write(json.dumps(item, separators=(",", ":")) + "\n")
                else:
                    f.write(item["url"] + "\n")
        print(f"\nSuccessfully added {len(results)} links to {output_file}.")

        if not args.keep_input:
            with open(input_file, "w"):
                pass
            print(f"Cleared {input_file}.")
    else:
        print("\nNo links were successfully converted.")


if __name__ == "__main__":
    main()
