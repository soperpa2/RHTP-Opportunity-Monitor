import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.database import get_supabase


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

RHTP_REQUIRED_TERMS = [
    "rural health transformation",
    "rural health transformation program",
    "rhtp"
]

PROCUREMENT_OPPORTUNITY_TERMS = [
    "request for proposals",
    "request for applications",
    "request for information",
    "request for qualifications",
    "rfp",
    "rfa",
    "rfi",
    "rfq",
    "nofo",
    "notice of funding",
    "funding opportunity",
    "grant opportunity",
    "solicitation",
    "bid",
    "contract opportunity",
    "procurement opportunity",
    "application deadline",
    "applications due",
    "letter of interest",
    "loi",
    "apply now",
    "application portal",
    "submit application",
    "funding available",
    "open opportunity",
    "current opportunities"
]

FOLLOW_LINK_TERMS = [
    "rural health transformation",
    "rhtp",
    "procurement",
    "grant",
    "funding",
    "opportunity",
    "rfp",
    "rfa",
    "rfi",
    "rfq",
    "nofo",
    "solicitation",
    "application",
    "letter of interest",
    "loi"
]

HARD_EXCLUDE_TERMS = [
    "mailto:",
    "tel:",
    "contact us",
    "staff directory",
    "directory",
    "newsletter",
    "calendar",
    "training",
    "webinar",
    "press release",
    "news release",
    "annual report",
    "meeting minutes",
    "agenda",
    "homepage",
    "home page",
    "about us",
    "general information",
    "construction",
    "janitorial",
    "landscaping",
    "roofing",
    "hvac",
    "vehicle",
    "fleet",
    "uniforms",
    "office supplies",
    "printing",
    "mailing",
    "parking",
    "plumbing",
    "elevator",
    "snow removal",
    "waste removal"
]


def normalize(text):
    return (text or "").lower().strip()


def has_any(text, terms):
    text = normalize(text)
    return any(term in text for term in terms)


def is_email_or_phone_link(url):
    url = normalize(url)
    return (
        url.startswith("mailto:")
        or url.startswith("tel:")
        or "mailto:" in url
        or "tel:" in url
    )


def is_excluded(text):
    text = normalize(text)
    if "@" in text and "http" not in text:
        return True
    return has_any(text, HARD_EXCLUDE_TERMS)


def is_direct_rhtp_opportunity(text, url):
    combined = normalize(f"{text} {url}")

    if is_email_or_phone_link(combined):
        return False

    if is_excluded(combined):
        return False

    has_rhtp = has_any(combined, RHTP_REQUIRED_TERMS)
    has_opportunity = has_any(combined, PROCUREMENT_OPPORTUNITY_TERMS)

    return has_rhtp and has_opportunity


def should_follow_link(link_text, href):
    combined = normalize(f"{link_text} {href}")

    if is_email_or_phone_link(combined):
        return False

    if is_excluded(combined):
        return False

    return has_any(combined, FOLLOW_LINK_TERMS)


def is_live_url(url):
    if is_email_or_phone_link(url):
        return False

    try:
        response = requests.head(
            url,
            headers=HEADERS,
            timeout=10,
            allow_redirects=True
        )
        return response.status_code < 400
    except Exception:
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=10,
                allow_redirects=True
            )
            return response.status_code < 400
        except Exception:
            return False


def fetch_page(url):
    response = requests.get(url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    return response.text


def extract_page_text_and_links(base_url, html):
    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(" ", strip=True)
    links = []

    for link in soup.find_all("a", href=True):
        link_text = link.get_text(" ", strip=True)
        href = urljoin(base_url, link["href"])

        if is_email_or_phone_link(href):
            continue

        if not href.startswith("http"):
            continue

        links.append({
            "text": link_text,
            "url": href
        })

    return page_text, links


def save_opportunity(
    supabase,
    source,
    url,
    title,
    description,
    raw_text
):
    existing = (
        supabase
        .table("raw_opportunities")
        .select("id")
        .eq("url", url)
        .execute()
        .data
    )

    if existing:
        supabase.table("raw_opportunities").update({
            "last_seen_at": "now()"
        }).eq("url", url).execute()

        print(f"Already known, updated last_seen_at: {url}")
        return False

    opportunity = {
        "source_id": source.get("id"),
        "state": source.get("state"),
        "agency": source.get("agency", "State Agency"),
        "title": title[:200] if title else url[:200],
        "url": url,
        "description": description[:500] if description else "",
        "raw_text": raw_text[:2000] if raw_text else "",
        "review_status": "new",
        "follow_up": False,
        "archived": False,
        "not_relevant": False
    }

    supabase.table("raw_opportunities").insert(opportunity).execute()

    print(f"Saved NEW direct RHTP opportunity: {opportunity['title']}")
    return True


def update_source_status(
    supabase,
    source_id,
    status,
    error=None,
    successful=False
):
    payload = {
        "last_crawl_status": status,
        "last_crawl_error": error
    }

    if successful:
        payload["last_successful_crawl_at"] = "now()"

    try:
        supabase.table("sources").update(payload).eq("id", source_id).execute()
    except Exception as status_error:
        print(f"Could not update source status: {status_error}")


def run_scraper():
    supabase = get_supabase()

    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    max_sources = int(os.getenv("MAX_SOURCES", "999"))
    max_links_per_source = int(os.getenv("MAX_LINKS_PER_SOURCE", "3"))

    print(f"TEST_MODE={test_mode}")
    print(f"MAX_SOURCES={max_sources}")
    print(f"MAX_LINKS_PER_SOURCE={max_links_per_source}")

    sources = (
        supabase
        .table("sources")
        .select("*")
        .eq("active", True)
        .eq("production_ready", True)
        .eq("opportunity_monitoring", True)
        .execute()
        .data
    )

    if test_mode:
        sources = sources[:max_sources]
        print(f"Test mode enabled. Limiting to {len(sources)} sources.")

    total_new_saved = 0
    total_known_seen = 0
    total_errors = 0
    visited_urls = set()

    for source in sources:
        state = source.get("state")
        url = source.get("url")
        source_id = source.get("id")

        print(f"\nCrawling {state}: {url}")

        try:
            html = fetch_page(url)
            visited_urls.add(url)

            page_text, links = extract_page_text_and_links(url, html)

            saved_count = 0
            known_count = 0
            followed_count = 0
            skipped_count = 0

            if is_direct_rhtp_opportunity(page_text, url) and is_live_url(url):
                was_new = save_opportunity(
                    supabase=supabase,
                    source=source,
                    url=url,
                    title=source.get("page_name") or f"{state} RHTP opportunity page",
                    description=page_text,
                    raw_text=page_text
                )

                if was_new:
                    saved_count += 1
                    total_new_saved += 1
                else:
                    known_count += 1
                    total_known_seen += 1

            candidate_links = []

            for link in links:
                link_text = link["text"]
                href = link["url"]
                combined_text = f"{link_text} {href}"

                if is_direct_rhtp_opportunity(combined_text, href) and is_live_url(href):
                    was_new = save_opportunity(
                        supabase=supabase,
                        source=source,
                        url=href,
                        title=link_text or href,
                        description=link_text,
                        raw_text=combined_text
                    )

                    if was_new:
                        saved_count += 1
                        total_new_saved += 1
                    else:
                        known_count += 1
                        total_known_seen += 1

                if should_follow_link(link_text, href):
                    candidate_links.append(link)
                else:
                    skipped_count += 1

            for link in candidate_links[:max_links_per_source]:
                follow_url = link["url"]

                if follow_url in visited_urls:
                    continue

                try:
                    print(f"Following: {follow_url}")
                    followed_count += 1
                    visited_urls.add(follow_url)

                    child_html = fetch_page(follow_url)
                    child_text, child_links = extract_page_text_and_links(
                        follow_url,
                        child_html
                    )

                    if is_direct_rhtp_opportunity(child_text, follow_url) and is_live_url(follow_url):
                        was_new = save_opportunity(
                            supabase=supabase,
                            source=source,
                            url=follow_url,
                            title=link["text"] or follow_url,
                            description=child_text,
                            raw_text=child_text
                        )

                        if was_new:
                            saved_count += 1
                            total_new_saved += 1
                        else:
                            known_count += 1
                            total_known_seen += 1

                    for child_link in child_links:
                        child_link_text = child_link["text"]
                        child_href = child_link["url"]
                        child_combined = f"{child_link_text} {child_href}"

                        if is_direct_rhtp_opportunity(child_combined, child_href) and is_live_url(child_href):
                            was_new = save_opportunity(
                                supabase=supabase,
                                source=source,
                                url=child_href,
                                title=child_link_text or child_href,
                                description=child_link_text,
                                raw_text=child_combined
                            )

                            if was_new:
                                saved_count += 1
                                total_new_saved += 1
                            else:
                                known_count += 1
                                total_known_seen += 1

                except Exception as child_error:
                    print(f"Follow-link error: {follow_url} | {child_error}")

            update_source_status(
                supabase,
                source_id=source_id,
                status="success",
                error=None,
                successful=True
            )

            print(
                f"Finished {state} — new saved {saved_count}, "
                f"known seen {known_count}, followed {followed_count}, skipped {skipped_count}"
            )

        except Exception as e:
            total_errors += 1
            error_message = str(e)

            update_source_status(
                supabase,
                source_id=source_id,
                status="error",
                error=error_message,
                successful=False
            )

            print("\n--- ERROR ---")
            print(f"State: {state}")
            print(f"URL: {url}")
            print(f"Error: {error_message}")
            print("------------\n")

    print("\nSCRAPER RUN COMPLETE")
    print(f"Sources attempted: {len(sources)}")
    print(f"New opportunities saved: {total_new_saved}")
    print(f"Known opportunities seen again: {total_known_seen}")
    print(f"Total source errors: {total_errors}")


if __name__ == "__main__":
    run_scraper()
