from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from urllib.parse import urljoin, urlparse
import re
import httpx
from bs4 import BeautifulSoup
import trafilatura
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import get_settings

BID_TERMS = [
    "bid", "bids", "solicitation", "solicitations", "rfp", "rfq", "rfi", "proposal", "proposals",
    "opportunity", "opportunities", "procurement", "vendor", "contract", "contracts", "eprocurement",
    "current", "business", "supplier"
]

@dataclass
class CrawledOpportunity:
    title: str
    url: str
    description: str
    raw_text: str
    source_url: str
    content_hash: str

def same_domain(base: str, candidate: str) -> bool:
    try:
        return urlparse(base).netloc.replace("www.", "") == urlparse(candidate).netloc.replace("www.", "")
    except Exception:
        return False

def looks_like_bid_link(text: str, href: str) -> bool:
    combined = f"{text} {href}".lower()
    return any(t in combined for t in BID_TERMS)

def clean_title(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:250] if text else "Untitled procurement opportunity"

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
def fetch(url: str) -> str:
    settings = get_settings()
    headers = {"User-Agent": settings.crawl_user_agent}
    with httpx.Client(timeout=settings.crawl_timeout_seconds, follow_redirects=True, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()
        ctype = response.headers.get("content-type", "")
        if "text" not in ctype and "html" not in ctype and "xml" not in ctype:
            return ""
        return response.text

def extract_text(html: str) -> str:
    extracted = trafilatura.extract(html) or ""
    if extracted:
        return extracted
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ")).strip()

def discover_links(base_url: str, html: str, max_links: int = 10) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        if not href.startswith("http"):
            continue
        if not same_domain(base_url, href):
            continue
        if looks_like_bid_link(a.get_text(" "), href):
            href = href.split("#")[0]
            if href not in links:
                links.append(href)
        if len(links) >= max_links:
            break
    return links

def page_to_opportunity(url: str, source_url: str, html: str) -> CrawledOpportunity | None:
    soup = BeautifulSoup(html, "html.parser")
    title = clean_title((soup.title.string if soup.title else "") or soup.find(["h1","h2"]).get_text(" ") if soup.find(["h1","h2"]) else "")
    raw_text = extract_text(html)
    if not raw_text or len(raw_text) < 80:
        return None
    lower = f"{title} {raw_text[:1000]}".lower()
    if not any(t in lower for t in BID_TERMS):
        return None
    description = raw_text[:1200]
    digest = sha256(f"{title}|{url}|{description}".encode("utf-8")).hexdigest()
    return CrawledOpportunity(title=title, url=url, description=description, raw_text=raw_text[:20000], source_url=source_url, content_hash=digest)

def crawl_source(source: dict) -> tuple[list[CrawledOpportunity], int, list[str]]:
    source_url = source["url"]
    max_links = int(source.get("max_links_to_follow") or 10)
    errors: list[str] = []
    visited = 0
    opportunities: list[CrawledOpportunity] = []
    try:
        home = fetch(source_url)
        visited += 1
    except Exception as e:
        return [], visited, [f"{source_url}: {e}"]

    links = discover_links(source_url, home, max_links=max_links)
    if not links:
        opp = page_to_opportunity(source_url, source_url, home)
        if opp:
            opportunities.append(opp)

    for link in links:
        try:
            html = fetch(link)
            visited += 1
            opp = page_to_opportunity(link, source_url, html)
            if opp:
                opportunities.append(opp)
        except Exception as e:
            errors.append(f"{link}: {e}")
    return opportunities, visited, errors
