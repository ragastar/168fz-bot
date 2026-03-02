"""Website and social media parsers using httpx + BeautifulSoup."""

import logging
import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

TIMEOUT = 15
MAX_TEXT_LENGTH = 15000
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.5",
}


def _trim(text: str) -> str:
    """Collapse whitespace and trim to MAX_TEXT_LENGTH."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH] + "..."
    return text


def _dedup_lines(lines: list[str]) -> list[str]:
    """Remove duplicate lines preserving order."""
    seen = set()
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            result.append(stripped)
    return result


def detect_url_type(url: str) -> str:
    """Detect social network type from URL.

    Returns: 'instagram', 'vk', 'telegram', or 'website'.
    """
    host = urlparse(url).hostname or ""
    host = host.lower().removeprefix("www.")

    if host in ("instagram.com", "instagr.am") or host.endswith(".instagram.com"):
        return "instagram"
    if host in ("vk.com", "vk.ru", "m.vk.com", "m.vk.ru"):
        return "vk"
    if host in ("t.me", "telegram.me", "telegram.org"):
        return "telegram"
    return "website"


async def parse_website(url: str) -> str:
    """Parse a generic website: title, meta, headings, paragraphs, nav, buttons, images."""
    async with httpx.AsyncClient(
        timeout=TIMEOUT, headers=HEADERS, follow_redirects=True, verify=False
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove scripts and styles
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    parts: list[str] = []

    # Title
    if soup.title and soup.title.string:
        parts.append(f"[TITLE] {soup.title.string.strip()}")

    # Meta description / og:description
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or meta.get("property") or "").lower()
        content = (meta.get("content") or "").strip()
        if name in ("description", "og:description", "og:title") and content:
            parts.append(f"[META:{name.upper()}] {content}")

    # Navigation text
    for nav in soup.find_all("nav"):
        nav_text = nav.get_text(" ", strip=True)
        if nav_text:
            parts.append(f"[NAV] {nav_text}")

    # Headings
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = tag.get_text(" ", strip=True)
        if text:
            parts.append(f"[{tag.name.upper()}] {text}")

    # Buttons and links-as-buttons
    for btn in soup.find_all(["button", "a"]):
        cls = " ".join(btn.get("class", []))
        text = btn.get_text(" ", strip=True)
        if text and ("btn" in cls or "button" in cls or btn.name == "button"):
            parts.append(f"[BUTTON] {text}")

    # Paragraphs and list items
    for tag in soup.find_all(["p", "li"]):
        text = tag.get_text(" ", strip=True)
        if text and len(text) > 3:
            parts.append(f"[TEXT] {text}")

    # Image alt texts
    for img in soup.find_all("img"):
        alt = (img.get("alt") or "").strip()
        if alt and len(alt) > 2:
            parts.append(f"[IMG_ALT] {alt}")

    parts = _dedup_lines(parts)
    result = "\n".join(parts)
    return _trim(result) if result else "[EMPTY] Не удалось извлечь текст со страницы."


async def parse_vk(url: str) -> str:
    """Parse a public VK page/group: name, description, wall posts."""
    async with httpx.AsyncClient(
        timeout=TIMEOUT, headers=HEADERS, follow_redirects=True, verify=False
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    parts: list[str] = []

    # Page/group name
    for sel in (".page_name", ".op_header", "h1", ".group_info_title"):
        el = soup.select_one(sel)
        if el:
            text = el.get_text(" ", strip=True)
            if text:
                parts.append(f"[VK_NAME] {text}")
                break

    # Description / status
    for sel in (".page_description", ".group_info_desc", ".status_text", ".page_status"):
        el = soup.select_one(sel)
        if el:
            text = el.get_text(" ", strip=True)
            if text:
                parts.append(f"[VK_DESC] {text}")

    # Wall posts
    for post in soup.select(".wall_post_text, .pi_text")[:15]:
        text = post.get_text(" ", strip=True)
        if text and len(text) > 5:
            parts.append(f"[VK_POST] {text}")

    # Fallback: if VK returned limited HTML, grab all visible text
    if len(parts) < 2:
        body_text = soup.get_text(" ", strip=True)
        if body_text:
            parts.append(f"[VK_BODY] {body_text}")

    parts = _dedup_lines(parts)
    result = "\n".join(parts)
    return _trim(result) if result else "[EMPTY] Не удалось извлечь данные со страницы VK."


async def parse_telegram(url: str) -> str:
    """Parse a public Telegram channel via t.me/s/ preview."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    # Ensure we use the /s/ (public preview) version
    if not path.startswith("s/"):
        channel = path.split("/")[0]
        url = f"https://t.me/s/{channel}"

    async with httpx.AsyncClient(
        timeout=TIMEOUT, headers=HEADERS, follow_redirects=True, verify=False
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    parts: list[str] = []

    # Channel name
    name_el = soup.select_one(".tgme_channel_info_header_title")
    if name_el:
        parts.append(f"[TG_NAME] {name_el.get_text(' ', strip=True)}")

    # Channel description
    desc_el = soup.select_one(".tgme_channel_info_description")
    if desc_el:
        parts.append(f"[TG_DESC] {desc_el.get_text(' ', strip=True)}")

    # Channel counters (subscribers etc.)
    for counter in soup.select(".tgme_channel_info_counter"):
        text = counter.get_text(" ", strip=True)
        if text:
            parts.append(f"[TG_STATS] {text}")

    # Posts
    for msg in soup.select(".tgme_widget_message_text")[:15]:
        text = msg.get_text(" ", strip=True)
        if text and len(text) > 5:
            parts.append(f"[TG_POST] {text}")

    parts = _dedup_lines(parts)
    result = "\n".join(parts)
    return _trim(result) if result else "[EMPTY] Не удалось извлечь данные Telegram-канала."
