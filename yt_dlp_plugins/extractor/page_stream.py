import hashlib
from urllib.parse import parse_qs, urlparse

from yt_dlp.extractor.common import InfoExtractor

from extractor.core import extract_media_url, page_has_video_stream_embed


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


def _stable_id(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]


class PageStreamIE(InfoExtractor):
    IE_NAME = "page_stream"
    IE_DESC = "Video pages with iframe embeds that expose HLS or MP4 stream URLs"
    _VALID_URL = r"https?://[^/]+/.+"

    @classmethod
    def suitable(cls, url):
        if not super().suitable(url):
            return False
        return page_has_video_stream_embed(url)

    def _real_extract(self, url):
        data = extract_media_url(url)
        if not data:
            self.raise_no_formats(
                "No supported video embed or stream URL found on this page"
            )

        media_url = data["url"]
        video_id = _stable_id(url)
        return {
            "id": video_id,
            "title": video_id,
            "formats": [
                {
                    "url": media_url,
                    "ext": _ext_from_url(media_url),
                    "http_headers": _media_headers(
                        data["referer"], data["origin"], data["user_agent"]
                    ),
                }
            ],
        }


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
        from extractor.core import USER_AGENT

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
