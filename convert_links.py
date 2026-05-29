#!/usr/bin/env python3
import urllib.request
import ssl
import re
import os
import argparse

def get_m3u8_link(url, base_url):
    # Create an unverified SSL context to bypass certificate errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8')
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

    # Extract the iframe that contains the video player
    match = re.search(r'src="([^"]*snstr(?:hls)?\.php\?fileid=[^"]+)"', html)
    if not match:
        print(f"Could not find iframe in {url}")
        return None
        
    iframe_url = match.group(1)
    if not iframe_url.startswith('http'):
        if iframe_url.startswith('//'):
            iframe_url = 'https:' + iframe_url
        else:
            iframe_url = f"{base_url.rstrip('/')}/" + iframe_url.lstrip('/')
            
    # Fetch the iframe content, making sure to pass the original URL as the Referer
    req2 = urllib.request.Request(iframe_url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Referer': url
    })
    try:
        html2 = urllib.request.urlopen(req2, context=ctx).read().decode('utf-8')
    except Exception as e:
        print(f"Failed to fetch iframe {iframe_url}: {e}")
        return None

    # Extract the m3u8 or mp4 link from the video source tag or jwplayer config
    m3u8_match = re.search(r'<source src="([^"]+\.(?:m3u8|mp4)[^"]*)"', html2)
    if not m3u8_match:
        m3u8_match = re.search(r'file\s*:\s*"([^"]+\.(?:m3u8|mp4)[^"]*)"', html2)
        
    if m3u8_match:
        # Some URLs might have HTML entities like &amp; instead of &
        return m3u8_match.group(1).replace('&amp;', '&')
    
    print(f"Could not find media link in {iframe_url}")
    return None

def main():
    parser = argparse.ArgumentParser(description="Extract m3u8/mp4 media links from URLs containing specific video iframes.")
    parser.add_argument('-i', '--input', required=True, help="Input file containing URLs (one per line)")
    parser.add_argument('-o', '--output', required=True, help="Output file to append extracted media links")
    parser.add_argument('-b', '--base-url', required=True, help="Base URL to use for relative iframe sources (e.g., https://example.com)")
    parser.add_argument('--keep-input', action='store_true', help="Do not clear the input file after processing")
    args = parser.parse_args()

    input_file = args.input
    output_file = args.output
    base_url = args.base_url

    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' does not exist.")
        return

    with open(input_file, 'r') as f:
        # Read lines, strip whitespace, and ignore empty lines
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        print(f"No URLs found in {input_file}.")
        return

    print(f"Found {len(urls)} URLs in {input_file}. Converting...")

    results = []
    for i, url in enumerate(urls, 1):
        print(f"Processing {i}/{len(urls)}: {url}")
        m3u8_link = get_m3u8_link(url, base_url)
        if m3u8_link:
            results.append(m3u8_link)
            print(f" -> Found: {m3u8_link}")
        else:
            print(f" -> Failed to extract.")

    if results:
        # Append the successfully converted links to output
        with open(output_file, 'a') as f:
            for link in results:
                f.write(link + '\n')
        print(f"\nSuccessfully added {len(results)} links to {output_file}.")
        
        if not args.keep_input:
            # Clear input file so we don't process the same links again next time
            with open(input_file, 'w') as f:
                pass
            print(f"Cleared {input_file}.")
    else:
        print("\nNo links were successfully converted.")

if __name__ == '__main__':
    main()
