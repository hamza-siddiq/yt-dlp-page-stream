import re
import ssl
import urllib.request
from typing import Optional
from urllib.parse import urlparse

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Matches iframe src on some video pages (remote script names: snstr.php, snstrhls.php)
VIDEO_PAGE_IFRAME_PATTERN = re.compile(
    r'src="([^"]*snstr(?:hls)?\.php\?fileid=[^"]+)"'
)
MEDIA_SOURCE_PATTERN = re.compile(
    r'<source src="([^"]+\.(?:m3u8|mp4)[^"]*)"'
)
JWPLAYER_FILE_PATTERN = re.compile(
    r'file\s*:\s*"([^"]+\.(?:m3u8|mp4)[^"]*)"'
)


def _ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _fetch(url: str, referer: Optional[str] = None) -> Optional[str]:
    headers = {"User-Agent": USER_AGENT}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    try:
        return urllib.request.urlopen(req, context=_ssl_context()).read().decode("utf-8")
    except Exception:
        return None


def _resolve_base_url(page_url: str, base_url: Optional[str]) -> str:
    if base_url:
        return base_url.rstrip("/")
    parsed = urlparse(page_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _origin_from_page(page_url: str) -> str:
    parsed = urlparse(page_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def page_has_video_stream_embed(page_url: str) -> bool:
    html = _fetch(page_url)
    if not html:
        return False
    return VIDEO_PAGE_IFRAME_PATTERN.search(html) is not None


def no_embed_hint(page_url: str) -> str:
    """Human-readable reason when extract_media_url returns None."""
    path = urlparse(page_url).path or ""
    if re.search(r"/page/\d+", path) or path.rstrip("/").endswith("/page"):
        return (
            "This URL looks like a listing or category page, not a single video. "
            "Use direct video page URLs (e.g. https://yoursite.com/12345/)."
        )
    return (
        "No supported video embed or stream URL found on this page "
        "(expected snstr.php / snstrhls.php iframe)."
    )


def extract_media_url(
    page_url: str, base_url: Optional[str] = None
) -> Optional[dict]:
    """
    Extract direct media URL and headers needed for CDN download.

    Returns dict with keys: url, referer, origin, user_agent, page, iframe_url
    """
    base = _resolve_base_url(page_url, base_url)
    origin = _origin_from_page(page_url)

    html = _fetch(page_url)
    if not html:
        return None

    match = VIDEO_PAGE_IFRAME_PATTERN.search(html)
    if not match:
        return None

    iframe_url = match.group(1)
    if not iframe_url.startswith("http"):
        if iframe_url.startswith("//"):
            iframe_url = "https:" + iframe_url
        else:
            iframe_url = f"{base}/" + iframe_url.lstrip("/")

    html2 = _fetch(iframe_url, referer=page_url)
    if not html2:
        return None

    media_match = MEDIA_SOURCE_PATTERN.search(html2)
    if not media_match:
        media_match = JWPLAYER_FILE_PATTERN.search(html2)
    if not media_match:
        return None

    media_url = media_match.group(1).replace("&amp;", "&")
    return {
        "url": media_url,
        "referer": page_url,
        "origin": origin,
        "user_agent": USER_AGENT,
        "page": page_url,
        "iframe_url": iframe_url,
    }
