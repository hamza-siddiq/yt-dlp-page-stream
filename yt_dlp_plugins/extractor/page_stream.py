import hashlib
import re
from urllib.parse import parse_qs, urlparse

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import ExtractorError

from extractor.core import (
    USER_AGENT,
    extract_all_media,
    no_embed_hint,
    page_has_extractable_media,
)

# Our own plugin extractors, skipped when checking for a dedicated handler.
_OUR_IE_NAMES = {"page_stream", "tokenized_cdn"}
_dedicated_classes = None


def _media_headers(referer, origin, user_agent):
    return {
        "Referer": referer,
        "Origin": origin,
        "User-Agent": user_agent,
    }


def _ext_from_url(url):
    if ".m3u8" in url.split("?")[0].lower():
        return "m3u8"
    return "mp4"


_HEIGHT_RE = re.compile(r"[_-](\d{3,4})p\b", re.IGNORECASE)


def _format_for(url, headers):
    fmt = {
        "url": url,
        "ext": _ext_from_url(url),
        "http_headers": headers,
    }
    match = _HEIGHT_RE.search(url)
    if match:
        fmt["height"] = int(match.group(1))
        fmt["format_id"] = f"{match.group(1)}p"
    return fmt


def _stable_id(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _has_dedicated_extractor(url):
    """True when any built-in (non-generic) yt-dlp extractor matches this URL.

    Lets page_stream sit between site-specific extractors and the generic
    fallback: dedicated extractors (YouTube, Vimeo, ...) keep handling their
    own URLs, and we only claim pages that would otherwise hit generic.
    """
    global _dedicated_classes
    if _dedicated_classes is None:
        from yt_dlp.extractor import gen_extractor_classes

        classes = []
        for ie in gen_extractor_classes():
            name = (getattr(ie, "IE_NAME", "") or "")
            if name.lower() == "generic" or name in _OUR_IE_NAMES:
                continue
            classes.append(ie)
        _dedicated_classes = classes

    for ie in _dedicated_classes:
        try:
            if ie.suitable(url):
                return True
        except Exception:
            continue
    return False


class PageStreamIE(InfoExtractor):
    IE_NAME = "page_stream"
    IE_DESC = (
        "Pages exposing direct HLS/MP4 media (incl. duplicated sources): "
        "de-duplicates and attaches Referer/Origin headers"
    )
    _VALID_URL = r"https?://[^/]+/.+"

    @classmethod
    def suitable(cls, url):
        if not super().suitable(url):
            return False
        # Defer to any site-specific extractor before doing network I/O.
        if _has_dedicated_extractor(url):
            return False
        return page_has_extractable_media(url)

    def _media_info(self, sources, headers, title):
        return {
            "id": _stable_id(sources[0]),
            "title": title,
            "http_headers": headers,
            "formats": [_format_for(url, headers) for url in sources],
        }

    def _real_extract(self, url):
        data = extract_all_media(url)
        if not data or not data.get("videos"):
            raise ExtractorError(no_embed_hint(url), expected=True)

        videos = data["videos"]
        headers = _media_headers(
            data["referer"], data["origin"], data["user_agent"]
        )
        title = data.get("title") or _stable_id(url)

        if len(videos) == 1:
            return self._media_info(videos[0], headers, title)

        entries = [
            self._media_info(sources, headers, f"{title} ({n})")
            for n, sources in enumerate(videos, 1)
        ]
        return self.playlist_result(
            entries, playlist_id=_stable_id(url), playlist_title=title
        )


class TokenizedCdnIE(InfoExtractor):
    IE_NAME = "tokenized_cdn"
    IE_DESC = (
        "Direct MP4/M3U8 CDN URLs with signed query parameters requiring Referer"
    )
    _VALID_URL = (
        r"https?://[^/]+/"
        r"(?P<id>[^/?#]+)\.(?P<ext>mp4|m3u8)\?[^#]*"
    )

    @classmethod
    def suitable(cls, url):
        if not super().suitable(url):
            return False
        parsed = urlparse(url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        keys = {k.lower() for k in query}
        return "token" in keys or "expires" in keys

    def _real_extract(self, url):
        referer_list = self._configuration_arg("referer")
        if not referer_list:
            self.raise_no_formats(
                "HTTP 428: this CDN requires a Referer. Pass the original page URL, e.g. "
                '--extractor-args "tokenized_cdn:referer=https://yoursite.com/video/..."'
            )

        referer = referer_list[0]
        mobj = self._match_valid_url(url)
        video_id = mobj.group("id")
        ext = mobj.group("ext")

        parsed = urlparse(referer)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        return {
            "id": video_id,
            "title": video_id,
            "formats": [
                {
                    "url": url,
                    "ext": ext,
                    "http_headers": _media_headers(referer, origin, USER_AGENT),
                }
            ],
        }
