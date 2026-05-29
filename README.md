# m3u8-link-extractor

Batch-extract direct **HLS (`.m3u8`)** and **MP4** stream URLs from web pages that embed `snstr.php` or `snstrhls.php` video iframes.

## Requirements

- Python 3.8+
- No third-party packages (stdlib only)

## Usage

```bash
python3 convert_links.py -i urls.txt -o streams.txt -b https://example.com
```

### Options

| Flag | Description |
|------|-------------|
| `-i`, `--input` | **Required.** Text file with page URLs, one per line |
| `-o`, `--output` | **Required.** File to append extracted media URLs to |
| `-b`, `--base-url` | **Required.** Site origin for resolving relative iframe paths (e.g. `https://example.com`) |
| `--keep-input` | Do not clear the input file after a successful run |

### Input format

One URL per line. Blank lines are ignored.

```
https://example.com/video/123/
https://example.com/video/456/
```

See [examples/urls.example.txt](examples/urls.example.txt).

## Behavior

1. For each URL in the input file, fetches the page and locates the video iframe.
2. Fetches the iframe player page (with the original URL as `Referer`).
3. Extracts the `.m3u8` or `.mp4` URL from the player HTML.
4. Appends successful extractions to the output file.
5. Clears the input file when at least one link was extracted, unless `--keep-input` is set.

## Limitations

- Only works on pages that use `snstr.php` / `snstrhls.php` embeds with the expected player markup.
- SSL certificate verification is disabled to tolerate hosts with invalid certs.
- Use only on content you are allowed to access.

## Publish to GitHub

```bash
cd m3u8-link-extractor
git init
git add .
git commit -m "Initial release of m3u8 link extractor CLI"
gh repo create m3u8-link-extractor --public --source=. --push
```

## License

MIT — see [LICENSE](LICENSE).
