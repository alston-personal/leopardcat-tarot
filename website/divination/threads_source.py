from __future__ import annotations

import html as html_lib
import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser


ALLOWED_THREADS_HOSTS = {"threads.net", "www.threads.net", "threads.com", "www.threads.com"}
MAX_HTML_BYTES = 512_000


class ThreadsSourceError(ValueError):
    pass


def _allowed_url(value: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(str(value or "").strip())
    except Exception:
        return False
    return parsed.scheme == "https" and (parsed.hostname or "").lower() in ALLOWED_THREADS_HOSTS


def is_threads_url(value: str) -> bool:
    if not _allowed_url(value):
        return False
    parsed = urllib.parse.urlparse(value)
    return bool(re.search(r"/(?:@[^/]+/)?post/[^/?#]+", parsed.path, re.I))


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.title_parts: list[str] = []
        self._in_title = False
        self._json_ld = False
        self.json_ld_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = {str(k).lower(): str(v or "") for k, v in attrs}
        if tag.lower() == "meta":
            key = (attrs.get("property") or attrs.get("name") or "").lower()
            content = attrs.get("content", "").strip()
            if key and content and key not in self.meta:
                self.meta[key] = content
        elif tag.lower() == "title":
            self._in_title = True
        elif tag.lower() == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self._json_ld = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False
        elif tag.lower() == "script":
            self._json_ld = False

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)
        if self._json_ld:
            self.json_ld_parts.append(data)


def _clean_text(value: str) -> str:
    value = html_lib.unescape(str(value or ""))
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _username_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    match = re.search(r"/@([^/]+)/post/", path, re.I)
    return match.group(1) if match else ""


def _author_from_title(title: str, username: str) -> str:
    title = _clean_text(title)
    patterns = [
        r"^(.+?)\s*\(@[^)]+\)\s+on\s+Threads",
        r"^(.+?)\s+on\s+Threads",
        r"^(.+?)\s*[|·-]\s*Threads",
    ]
    for pattern in patterns:
        match = re.search(pattern, title, re.I)
        if match:
            candidate = _clean_text(match.group(1)).strip('"“” ')
            if candidate:
                return candidate
    return f"@{username}" if username else "Threads 作者"


def _extract_json_ld(parts: list[str]) -> tuple[str, str]:
    raw = "\n".join(parts).strip()
    if not raw:
        return "", ""
    try:
        payload = json.loads(raw)
    except Exception:
        return "", ""
    nodes = payload if isinstance(payload, list) else [payload]
    for node in nodes:
        if not isinstance(node, dict):
            continue
        text = node.get("articleBody") or node.get("text") or node.get("description") or ""
        author = node.get("author") or ""
        if isinstance(author, dict):
            author = author.get("name") or author.get("alternateName") or ""
        if text:
            return _clean_text(str(text)), _clean_text(str(author))
    return "", ""


def parse_threads_html(raw_html: str, source_url: str) -> dict:
    parser = _MetaParser()
    parser.feed(raw_html)
    username = _username_from_url(source_url)
    title = parser.meta.get("og:title") or parser.meta.get("twitter:title") or _clean_text("".join(parser.title_parts))
    text = (
        parser.meta.get("og:description")
        or parser.meta.get("twitter:description")
        or parser.meta.get("description")
        or ""
    )
    ld_text, ld_author = _extract_json_ld(parser.json_ld_parts)
    text = _clean_text(ld_text or text)
    author = _clean_text(ld_author) or _author_from_title(title, username)
    if not text:
        raise ThreadsSourceError("threads_post_text_unavailable")
    return {
        "type": "threads",
        "url": source_url,
        "author": author,
        "username": username,
        "text": text,
    }


def resolve_threads_url(url: str, timeout: float = 8.0) -> dict:
    url = str(url or "").strip()
    if not is_threads_url(url):
        raise ThreadsSourceError("invalid_threads_url")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LeopardCatTarot/1.0; +https://leopardcat-tarot.milkcat.org/)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8,ja;q=0.7",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            final_url = response.geturl()
            if not _allowed_url(final_url):
                raise ThreadsSourceError("threads_redirect_not_allowed")
            raw = response.read(MAX_HTML_BYTES + 1)
            if len(raw) > MAX_HTML_BYTES:
                raise ThreadsSourceError("threads_page_too_large")
            charset = response.headers.get_content_charset() or "utf-8"
    except ThreadsSourceError:
        raise
    except Exception as exc:
        raise ThreadsSourceError("threads_fetch_failed") from exc
    return parse_threads_html(raw.decode(charset, errors="replace"), final_url)
