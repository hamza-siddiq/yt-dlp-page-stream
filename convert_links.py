#!/usr/bin/env python3
import argparse
import json
import os

from cli_ui import get_console, print_msg
from extractor.core import extract_media_url


def _extract_urls(urls, base_url):
    results = []
    console = get_console()

    if console:
        from rich.progress import (
            BarColumn,
            Progress,
            SpinnerColumn,
            TaskProgressColumn,
            TextColumn,
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Extracting streams", total=len(urls))
            for url in urls:
                progress.update(task, description=url[:80])
                extracted = extract_media_url(url, base_url)
                if extracted:
                    results.append(extracted)
                    progress.console.print(
                        f"  [green]✓[/green] {extracted['url']}"
                    )
                else:
                    progress.console.print(f"  [red]✗[/red] {url}")
                progress.advance(task)
    else:
        for i, url in enumerate(urls, 1):
            print(f"Processing {i}/{len(urls)}: {url}")
            extracted = extract_media_url(url, base_url)
            if extracted:
                results.append(extracted)
                print(f" -> Found: {extracted['url']}")
            else:
                print(" -> Failed to extract.")

    return results


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
        print_msg(f"Input file '{input_file}' does not exist.", style="red")
        return

    with open(input_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        print_msg(f"No URLs found in {input_file}.", style="yellow")
        return

    print_msg(
        f"Found {len(urls)} URLs in {input_file}. Converting...",
        style="bold",
    )

    results = _extract_urls(urls, args.base_url)

    if results:
        with open(output_file, "a") as f:
            for item in results:
                if args.format == "jsonl":
                    f.write(json.dumps(item, separators=(",", ":")) + "\n")
                else:
                    f.write(item["url"] + "\n")
        print_msg(
            f"Successfully added {len(results)}/{len(urls)} links to {output_file}.",
            style="bold green",
        )

        if not args.keep_input:
            with open(input_file, "w"):
                pass
            print_msg(f"Cleared {input_file}.", style="dim")
    else:
        print_msg("No links were successfully converted.", style="yellow")


if __name__ == "__main__":
    main()
