import ipaddress
import socket
import threading
from urllib.parse import quote_plus, urlparse

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

_lock = threading.RLock()
_pw: Playwright | None = None
_context: BrowserContext | None = None
_page: Page | None = None


def _safe_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only public HTTP/HTTPS URLs are allowed.")
    host = parsed.hostname.lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        raise ValueError("Local/private addresses are blocked.")
    try:
        for info in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80)):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                raise ValueError("Local/private addresses are blocked.")
    except socket.gaierror as exc:
        raise ValueError("Hostname could not be resolved.") from exc
    return url


def _get_page() -> Page:
    global _pw, _context, _page
    with _lock:
        if _page and not _page.is_closed():
            return _page
        _pw = sync_playwright().start()
        # Uses installed Google Chrome when available and keeps automation isolated
        # from the user's normal Chrome profile/cookies.
        _context = _pw.chromium.launch_persistent_context(
            user_data_dir="data/browser_profile",
            channel="chrome",
            headless=False,
            args=["--autoplay-policy=no-user-gesture-required"],
        )
        _page = _context.pages[0] if _context.pages else _context.new_page()
        return _page


def open_url(url: str) -> dict:
    safe = _safe_public_url(url)
    page = _get_page()
    page.goto(safe, wait_until="domcontentloaded", timeout=30000)
    return {"ok": True, "url": page.url, "title": page.title()}


def search_web(query: str) -> dict:
    if not query.strip():
        raise ValueError("Search query is required.")
    return open_url(f"https://www.google.com/search?q={quote_plus(query[:200])}")


def play_youtube(query: str) -> dict:
    if not query.strip():
        raise ValueError("YouTube query is required.")
    page = _get_page()
    page.goto(f"https://www.youtube.com/results?search_query={quote_plus(query[:200])}", wait_until="domcontentloaded", timeout=30000)
    try:
        first = page.locator("a#video-title").first
        first.wait_for(state="visible", timeout=15000)
        title = (first.get_attribute("title") or first.inner_text() or query).strip()
        first.click()
        page.wait_for_url("**/watch?**", timeout=15000)
        try:
            page.locator("video").evaluate("el => el.play()")
        except Exception:
            pass
        return {"ok": True, "url": page.url, "title": title, "playing": True}
    except Exception as exc:
        raise RuntimeError("YouTube search opened, but a playable video could not be started.") from exc


def media_action(action: str) -> dict:
    page = _get_page()
    if "youtube.com/watch" not in page.url:
        raise ValueError("Open a YouTube video first.")
    js = "el => el.pause()" if action == "pause" else "el => el.play()"
    try:
        page.locator("video").evaluate(js)
    except Exception as exc:
        raise RuntimeError(f"Could not {action} the current video.") from exc
    return {"ok": True, "action": action, "url": page.url}
