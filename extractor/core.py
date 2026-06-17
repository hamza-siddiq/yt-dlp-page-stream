import re
import ssl
import time
import urllib.error
import urllib.request
from html import unescape
from typing import Optional
from urllib.parse import urlparse

_FETCH_TIMEOUT = 15
_FETCH_RETRIES = 2
_FETCH_BACKOFF = 0.8

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Matches iframe src on some video pages (remote script names: snstr.php, snstrhls.php)
VIDEO_PAGE_IFRAME_PATTERN = re.compile(
    r'src="([^"]*snstr(?:hls)?\.php\?fileid=[^"]+)"'
)
# Direct media URLs commonly embedded in a page or its player iframe. Each
# pattern captures an .m3u8/.mp4 URL; together they let us extract media from
# arbitrary pages (not just one site) and de-duplicate the results.
MEDIA_SOURCE_PATTERN = re.compile(
    r'<source\b[^>]*\bsrc=["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
    re.IGNORECASE,
)
JWPLAYER_FILE_PATTERN = re.compile(
    r'\bfile\s*:\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
    re.IGNORECASE,
)
_OG_VIDEO_PATTERN = re.compile(
    r'<meta\b[^>]*\bproperty=["\']og:video(?::(?:url|secure_url))?["\']'
    r'[^>]*\bcontent=["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
    re.IGNORECASE,
)
_OG_VIDEO_PATTERN_REV = re.compile(
    r'<meta\b[^>]*\bcontent=["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']'
    r'[^>]*\bproperty=["\']og:video(?::(?:url|secure_url))?["\']',
    re.IGNORECASE,
)
# A <video> element groups its <source> children: multiple <source>s are
# alternate qualities of ONE video, not separate videos.
_VIDEO_BLOCK_PATTERN = re.compile(r"<video\b([^>]*)>(.*?)</video>", re.IGNORECASE | re.DOTALL)
_VIDEO_SRC_ATTR = re.compile(
    r'\bsrc=["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', re.IGNORECASE
)
# Page-level media not wrapped in a <video> element (each is its own video).
_PAGE_MEDIA_PATTERNS = (_OG_VIDEO_PATTERN, _OG_VIDEO_PATTERN_REV, JWPLAYER_FILE_PATTERN)

_OG_TITLE_PATTERN = re.compile(
    r'<meta\b[^>]*\bproperty=["\']og:title["\'][^>]*\bcontent=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_TITLE_PATTERN_REV = re.compile(
    r'<meta\b[^>]*\bcontent=["\']([^"\']+)["\'][^>]*\bproperty=["\']og:title["\']',
    re.IGNORECASE,
)
_TITLE_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

# Small cache so suitable() and _real_extract() do not fetch the same page twice.
_PAGE_CACHE: "dict[tuple, Optional[str]]" = {}
_PAGE_CACHE_MAX = 64


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
    ctx = _ssl_context()
    for attempt in range(_FETCH_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=_FETCH_TIMEOUT) as resp:
                return resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError:
            return None  # definitive HTTP status (404, 403, ...): do not retry
        except Exception:
            # Connection reset / timeout / transient error: back off and retry.
            if attempt < _FETCH_RETRIES:
                time.sleep(_FETCH_BACKOFF * (attempt + 1))
    return None


def _fetch_cached(url: str, referer: Optional[str] = None) -> Optional[str]:
    key = (url, referer)
    if key in _PAGE_CACHE:
        return _PAGE_CACHE[key]
    html = _fetch(url, referer=referer)
    if len(_PAGE_CACHE) >= _PAGE_CACHE_MAX:
        _PAGE_CACHE.clear()
    _PAGE_CACHE[key] = html
    return html


def _resolve_base_url(page_url: str, base_url: Optional[str]) -> str:
    if base_url:
        return base_url.rstrip("/")
    parsed = urlparse(page_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _origin_from_page(page_url: str) -> str:
    parsed = urlparse(page_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _absolutize(src: str, base: str) -> str:
    if src.startswith("http"):
        return src
    if src.startswith("//"):
        return "https:" + src
    return f"{base}/" + src.lstrip("/")


def _norm(url: str) -> str:
    return url.replace("&amp;", "&")


def _collect_videos(html: str) -> "list[list[str]]":
    """Return videos from one page as lists of source URLs, in document order.

    Each inner list is one video's alternate-quality sources (the <source>
    children of a <video>, or a single page-level media URL). Pages that embed
    the same video twice (e.g. lightbox + inline player) collapse to one entry
    because identical source sets are de-duplicated.
    """
    found = []  # (document_position, [source urls])
    block_spans = []
    for block in _VIDEO_BLOCK_PATTERN.finditer(html):
        block_spans.append((block.start(), block.end()))
        attrs, inner = block.group(1), block.group(2)
        sources = [m.group(1) for m in MEDIA_SOURCE_PATTERN.finditer(inner)]
        attr_src = _VIDEO_SRC_ATTR.search(attrs)
        if attr_src:
            sources.insert(0, attr_src.group(1))
        if sources:
            found.append((block.start(), sources))

    def _inside_video_block(pos: int) -> bool:
        return any(start <= pos < end for start, end in block_spans)

    # Bare <source> outside any <video> (rare) and page-level media (og:video,
    # JWPlayer) — each is treated as its own single-source video.
    for match in MEDIA_SOURCE_PATTERN.finditer(html):
        if not _inside_video_block(match.start()):
            found.append((match.start(), [match.group(1)]))
    for pattern in _PAGE_MEDIA_PATTERNS:
        for match in pattern.finditer(html):
            found.append((match.start(), [match.group(1)]))

    found.sort(key=lambda item: item[0])

    seen = set()
    videos = []
    for _, sources in found:
        urls = list(dict.fromkeys(_norm(u) for u in sources))
        key = frozenset(urls)
        if key in seen:
            continue
        seen.add(key)
        videos.append(urls)
    return videos


def _page_title(html: str) -> Optional[str]:
    for pattern in (_OG_TITLE_PATTERN, _OG_TITLE_PATTERN_REV, _TITLE_PATTERN):
        match = pattern.search(html)
        if match:
            title = unescape(re.sub(r"\s+", " ", match.group(1)).strip())
            if title:
                return title
    return None


def page_has_video_stream_embed(page_url: str) -> bool:
    """Backwards-compatible check for the snstr.php iframe embed only."""
    html = _fetch_cached(page_url)
    if not html:
        return False
    return VIDEO_PAGE_IFRAME_PATTERN.search(html) is not None


def page_has_extractable_media(page_url: str, base_url: Optional[str] = None) -> bool:
    """True when the page exposes at least one direct .mp4/.m3u8 media URL."""
    return extract_all_media(page_url, base_url) is not None


def no_embed_hint(page_url: str) -> str:
    """Human-readable reason when no media URL could be extracted."""
    path = urlparse(page_url).path or ""
    if re.search(r"/page/\d+", path) or path.rstrip("/").endswith("/page"):
        return (
            "This URL looks like a listing or category page, not a single video. "
            "Use direct video page URLs (e.g. https://yoursite.com/12345/)."
        )
    return (
        "No downloadable video media (.mp4 or .m3u8) found on this page. "
        "The page may use an unsupported player or require JavaScript."
    )


def extract_all_media(
    page_url: str, base_url: Optional[str] = None
) -> Optional[dict]:
    """Extract every unique video from a page (and its player iframe).

    Returns a dict with keys: title, videos (list of de-duplicated videos, each
    a list of alternate-quality source URLs in document order), referer, origin,
    user_agent, iframe_url. Returns None when the page exposes no direct media.
    """
    base = _resolve_base_url(page_url, base_url)
    origin = _origin_from_page(page_url)

    html = _fetch_cached(page_url)
    if not html:
        return None

    videos = _collect_videos(html)

    iframe_url = None
    iframe_match = VIDEO_PAGE_IFRAME_PATTERN.search(html)
    if iframe_match:
        iframe_url = _absolutize(iframe_match.group(1), base)
        iframe_html = _fetch_cached(iframe_url, referer=page_url)
        if iframe_html:
            videos.extend(_collect_videos(iframe_html))

    # De-duplicate again across page + iframe by source set.
    seen = set()
    unique = []
    for sources in videos:
        key = frozenset(sources)
        if key in seen:
            continue
        seen.add(key)
        unique.append(sources)

    if not unique:
        return None

    return {
        "title": _page_title(html),
        "videos": unique,
        "referer": page_url,
        "origin": origin,
        "user_agent": USER_AGENT,
        "iframe_url": iframe_url,
    }


def extract_media_url(
    page_url: str, base_url: Optional[str] = None
) -> Optional[dict]:
    """Extract the first direct media URL and headers for CDN download.

    Kept for the page-stream-extract CLI; returns the same dict shape as before
    (url, referer, origin, user_agent, page, iframe_url).
    """
    data = extract_all_media(page_url, base_url)
    if not data:
        return None
    return {
        "url": data["videos"][0][0],
        "referer": data["referer"],
        "origin": data["origin"],
        "user_agent": data["user_agent"],
        "page": page_url,
        "iframe_url": data["iframe_url"],
    }
