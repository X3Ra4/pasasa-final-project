import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from typing import Any
from urllib import error, parse, request

from django.core.cache import cache


logger = logging.getLogger(__name__)

STEAM_SOURCE = "steam"
ARK_SURVIVAL_ASCENDED_APP_ID = 2399830
STEAM_NEWS_URL = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"
SUPPORTED_LANGUAGES = {"en", "ru"}
DEFAULT_LANGUAGE = "ru"
FALLBACK_LANGUAGE = "en"
NEWS_CACHE_TIMEOUT = 60 * 15
SOURCE_FETCH_TIMEOUT = 8
TRANSLATION_TIMEOUT = 8
DEFAULT_NEWS_LIMIT = 4
MAX_DESCRIPTION_LENGTH = 280


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)

    def get_text(self) -> str:
        return "".join(self.parts)


class _ImageSourceExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        attrs_map = dict(attrs)
        src = attrs_map.get("src")
        if src:
            self.sources.append(src)


def resolve_news_language(lang: str | None) -> str:
    if not lang:
        return DEFAULT_LANGUAGE
    normalized = lang.strip().lower()
    if normalized in SUPPORTED_LANGUAGES:
        return normalized
    logger.warning("Unsupported news language requested: %s. Falling back to %s.", lang, FALLBACK_LANGUAGE)
    return FALLBACK_LANGUAGE


def get_news_payload(lang: str | None = None) -> dict[str, Any]:
    resolved_lang = resolve_news_language(lang)
    cache_key = f"news_payload:{STEAM_SOURCE}:{resolved_lang}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        raw_items = fetch_steam_news()
        normalized_items = [normalize_steam_news_item(item) for item in raw_items]
        localized_items = localize_news_items(normalized_items, resolved_lang)
    except Exception:
        logger.exception("Failed to build news payload for lang=%s", resolved_lang)
        localized_items = []

    payload = {
        "lang": resolved_lang,
        "source": STEAM_SOURCE,
        "items": localized_items,
    }
    cache.set(cache_key, payload, timeout=NEWS_CACHE_TIMEOUT)
    return payload


def fetch_steam_news(
    *,
    app_id: int = ARK_SURVIVAL_ASCENDED_APP_ID,
    count: int = DEFAULT_NEWS_LIMIT,
    timeout: int = SOURCE_FETCH_TIMEOUT,
) -> list[dict[str, Any]]:
    query = parse.urlencode(
        {
            "appid": app_id,
            "count": count,
            "maxlength": 0,
            "feeds": "steam_community_announcements",
            "format": "json",
        }
    )
    url = f"{STEAM_NEWS_URL}?{query}"
    req = request.Request(url, headers={"User-Agent": "PASASA-NewsBot/1.0"})

    try:
        with request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        logger.exception("Failed to fetch Steam news from %s", url)
        return []

    return payload.get("appnews", {}).get("newsitems", []) or []


def normalize_steam_news_item(item: dict[str, Any]) -> dict[str, Any]:
    title = clean_text(item.get("title", ""))
    body = clean_text(item.get("contents", ""))
    url = item.get("url") or build_steam_news_url(item)
    image = extract_image_url(item.get("contents", ""))
    published_at = to_iso_datetime(item.get("date"))
    steam_gid = str(item.get("gid") or "").strip()

    return {
        "id": build_stable_id(steam_gid, url, title),
        "title": title,
        "description": shorten_text(body),
        "url": url,
        "image": image,
        "published_at": published_at,
    }


def localize_news_items(items: list[dict[str, Any]], lang: str) -> list[dict[str, Any]]:
    if lang == "en":
        return items

    return [localize_news_item(item, lang) for item in items]


def localize_news_item(item: dict[str, Any], lang: str) -> dict[str, Any]:
    if lang != "ru":
        return item

    localized = dict(item)
    localized["title"] = translate_news_text(item["title"], target_lang=lang)
    localized["description"] = translate_news_text(item["description"], target_lang=lang)
    return localized


def translate_news_text(text: str, *, target_lang: str) -> str:
    clean = text.strip()
    if not clean:
        return clean
    if target_lang == "en":
        return clean
    if target_lang == "ru" and looks_russian(clean):
        return clean

    translated = translate_with_google(clean, target_lang=target_lang)
    if translated:
        return translated

    translated = translate_with_libretranslate(clean, target_lang=target_lang)
    if translated:
        return translated
    return clean


def translate_with_google(text: str, *, target_lang: str) -> str | None:
    query = parse.urlencode(
        {
            "client": "gtx",
            "sl": "en",
            "tl": target_lang,
            "dt": "t",
            "q": text,
        }
    )
    req = request.Request(
        f"{GOOGLE_TRANSLATE_URL}?{query}",
        headers={
            "User-Agent": "PASASA-NewsBot/1.0",
        },
    )

    try:
        with request.urlopen(req, timeout=TRANSLATION_TIMEOUT) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        logger.exception("Google news translation failed for target_lang=%s", target_lang)
        return None

    if not isinstance(response_payload, list) or not response_payload:
        logger.warning("Google translation returned unexpected payload for target_lang=%s", target_lang)
        return None

    parts = response_payload[0]
    if not isinstance(parts, list):
        return None

    translated_parts: list[str] = []
    for part in parts:
        if isinstance(part, list) and part:
            translated_text = part[0]
            if isinstance(translated_text, str):
                translated_parts.append(translated_text)

    translated = "".join(translated_parts).strip()
    if not translated:
        logger.warning("Google translation returned empty response for target_lang=%s", target_lang)
        return None
    return clean_text(translated)


def translate_with_libretranslate(text: str, *, target_lang: str) -> str | None:
    api_url = os.getenv("NEWS_TRANSLATION_API_URL", "").strip()
    if not api_url:
        return None

    payload = {
        "q": text,
        "source": "en",
        "target": target_lang,
        "format": "text",
    }
    api_key = os.getenv("NEWS_TRANSLATION_API_KEY", "").strip()
    if api_key:
        payload["api_key"] = api_key

    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        api_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "PASASA-NewsBot/1.0",
        },
    )

    try:
        with request.urlopen(req, timeout=TRANSLATION_TIMEOUT) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        logger.exception("News translation failed for target_lang=%s", target_lang)
        return None

    translated = response_payload.get("translatedText")
    if not translated:
        logger.warning("Translation API returned empty response for target_lang=%s", target_lang)
        return None
    return clean_text(translated)


def clean_text(value: str) -> str:
    if not value:
        return ""
    text = value
    text = re.sub(r"\[img\].*?\[/img\]", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\[url=.*?\](.*?)\[/url\]", r"\1", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\[/?(?:b|i|u|h1|h2|h3|list|\*|quote|spoiler)\]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[(?:color|quote|url|img|previewyoutube|previewyoutubehd|table|tr|td|th|code|noparse)(?:=[^\]]*)?\]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[/(?:color|quote|url|img|previewyoutube|previewyoutubehd|table|tr|td|th|code|noparse)\]", " ", text, flags=re.IGNORECASE)
    text = text.replace("{STEAM_CLAN_IMAGE}", " ")
    plain = strip_html(text)
    plain = unescape(plain)
    plain = re.sub(r"\[[^\]]+\]", " ", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain


def strip_html(value: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(value)
    parser.close()
    return parser.get_text()


def shorten_text(value: str, limit: int = MAX_DESCRIPTION_LENGTH) -> str:
    if len(value) <= limit:
        return value
    shortened = value[:limit].rsplit(" ", 1)[0].strip()
    return f"{shortened}..."


def extract_image_url(value: str) -> str | None:
    if not value:
        return None

    parser = _ImageSourceExtractor()
    try:
        parser.feed(value)
        parser.close()
    except Exception:
        logger.exception("Failed to parse image sources from Steam news body.")

    candidates = list(parser.sources)

    bbcode_image_matches = re.findall(r"\[img\](.*?)\[/img\]", value, flags=re.IGNORECASE | re.DOTALL)
    candidates.extend(bbcode_image_matches)

    steam_clan_matches = re.findall(
        r"\{STEAM_CLAN_IMAGE\}/([^\s\]\"']+\.(?:jpg|jpeg|png|webp|gif))",
        value,
        flags=re.IGNORECASE,
    )
    candidates.extend(f"https://clan.akamai.steamstatic.com/images/{match.lstrip('/')}" for match in steam_clan_matches)

    url_matches = re.findall(r"https?://[^\s\"']+\.(?:jpg|jpeg|png|webp|gif)", value, flags=re.IGNORECASE)
    candidates.extend(url_matches)

    for candidate in candidates:
        normalized = normalize_image_url(candidate)
        if normalized:
            return normalized
    return None


def normalize_image_url(value: str | None) -> str | None:
    if not value:
        return None
    candidate = unescape(value).strip()
    if candidate.startswith("//"):
        candidate = f"https:{candidate}"
    if candidate.startswith("{STEAM_CLAN_IMAGE}/"):
        candidate = candidate.replace("{STEAM_CLAN_IMAGE}/", "https://clan.akamai.steamstatic.com/images/", 1)
    candidate = candidate.split()[0].strip("\"'()[]{}<>,")
    if not re.match(r"^https?://", candidate, flags=re.IGNORECASE):
        return None
    if not re.search(r"\.(?:jpg|jpeg|png|webp|gif)(?:\?.*)?$", candidate, flags=re.IGNORECASE):
        return None
    return candidate


def build_steam_news_url(item: dict[str, Any]) -> str:
    gid = item.get("gid")
    if gid:
        return f"https://store.steampowered.com/news/app/{ARK_SURVIVAL_ASCENDED_APP_ID}/view/{gid}"
    return f"https://store.steampowered.com/app/{ARK_SURVIVAL_ASCENDED_APP_ID}/"


def to_iso_datetime(timestamp: Any) -> str | None:
    if not timestamp:
        return None
    try:
        dt = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None
    return dt.isoformat().replace("+00:00", "Z")


def build_stable_id(steam_gid: str, url: str, title: str) -> str:
    if steam_gid:
        return f"{STEAM_SOURCE}:{steam_gid}"
    digest = hashlib.sha256(f"{url}|{title}".encode("utf-8")).hexdigest()[:16]
    return f"{STEAM_SOURCE}:{digest}"


def looks_russian(text: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", text))
