import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from app.database import get_supabase


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

HIGH_PRIORITY = [
    "rural health transformation",
    "rural health transformation program",
    "rhtp",
    "medicaid transformation",
    "value-based care"
]

HEALTH_TERMS = [
    "rural health",
    "rhtp",
    "rural health transformation",
    "medicaid",
    "telehealth",
    "telemedicine",
    "behavioral health",
    "public health",
    "health workforce",
    "care coordination",
    "remote patient monitoring",
    "mobile health",
    "food as medicine",
    "health information exchange",
    "interoperability",
    "fqhc",
    "rural hospital",
    "community health",
    "population health",
    "maternal health",
    "substance use",
    "opioid",
    "grant",
    "funding",
    "procurement",
    "request for proposals",
    "rfp",
    "rfa",
    "notice of funding",
    "application"
]

EXCLUDE = [
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
    "propane",
    "travel services",
    "p-card",
    "card program",
    "parking",
    "elevator",
    "plumbing",
    "waste removal",
    "snow removal"
]

FOLLOW_LINK_TERMS = [
    "rural",
    "health",
    "medicaid",
    "grant",
    "funding",
    "procurement",
    "rfp",
    "rfa",
    "solicitation",
    "opportunity",
    "application",
    "program",
    "public notice"
]


def normalize(text):
    return (text or "").lower().strip()


def has_health_term(text):
    text = normalize(text)
    return any(term in text for term in HEALTH_TERMS)


def score_text(text):
    text = normalize(text)
    score = 0

    for phrase in HIGH_PRIORITY:
        if phrase in text:
            score += 5

    for term in HEALTH_TERMS:
        if term in text:
            score += 2

    for bad in EXCLUDE:
        if bad in text:
            score -= 5

    return score


def should_follow_link(link_text, href):
    combined = normalize(f"{link_text} {href}")
    return any(term in combined for term in FOLLOW_LINK_TERMS)


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

        if href.startswith("mailto:") or href.startswith("tel:"):
            continue

        if not href.startswith("http"):
            continue

        links.append({
            "text": link_text,
            "url": href
        })

    return page_text, links


def save_opportunity(supabase, source, url, title, description, raw_text):
    opportunity = {
        "source_id": source.get("id"),
        "state": source.get("state"),
        "agency": source.get("agency", "State Agency"),
        "title": title[:200] if title else url[:200],
        "url": url,
        "description": description[:500] if description else "",
        "raw_text": raw_text[:2000] if raw_text else ""
    }

    supabase.table("raw_opportunities").upsert(
        opportunity,
        on_conflict="url"
    ).execute()


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
    max_links_per_source = int(os.getenv("MAX_LINKS_PER_SOURCE", "5"))

    print(f"TEST_MODE={test_mode}")
    print(f"MAX_SOURCES={max_sources}")
    print(f"MAX_LINKS_PER_SOURCE={max_links_per_source}")

    sources = (
        supabase
        .table("sources")
        .select("*")
        .eq("active", True)
        .execute()
        .data
    )

    production_ready_sources = [
        source for source in sources
        if source.get("production_ready") is True
    ]

    if production_ready_sources:
        sources = production_ready_sources
        print(f"Using production-ready sources: {len(sources)}")
    else:
        print("No production-ready sources found. Falling back to all active sources.")

    if test_mode:
        sources = sources[:max_sources]
        print(f"Test mode enabled. Limiting to {len(sources)} sources.")

    total_saved = 0
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
            skipped_count = 0
            followed_count = 0

            source_page_score = score_text(page_text)

            if source_page_score >= 6 and has_health_term(page_text):
                save_opportunity(
                    supabase=supabase,
                    source=source,
                    url=url,
                    title=source.get("page_name") or f"{state} relevant source page",
                    description=page_text,
                    raw_text=page_text
                )
                saved_count += 1
                total_saved += 1
                print(f"Saved source page score={source_page_score}: {url}")

            candidate_links = []
            for link in links:
                link_text = link["text"]
                href = link["url"]
                combined_text = f"{link_text} {href}"
                score = score_text(combined_text)

                if score >= 6 and has_health_term(combined_text):
                    save_opportunity(
                        supabase=supabase,
                        source=source,
                        url=href,
                        title=link_text or href,
                        description=link_text,
                        raw_text=combined_text
                    )
                    saved_count += 1
                    total_saved += 1
                    print(f"Saved link score={score}: {link_text or href}")

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

                    child_score = score_text(child_text)

                    if child_score >= 6 and has_health_term(child_text):
                        save_opportunity(
                            supabase=supabase,
                            source=source,
                            url=follow_url,
                            title=link["text"] or follow_url,
                            description=child_text,
                            raw_text=child_text
                        )
                        saved_count += 1
                        total_saved += 1
                        print(f"Saved followed page score={child_score}: {follow_url}")

                    for child_link in child_links:
                        child_link_text = child_link["text"]
                        child_href = child_link["url"]
                        child_combined = f"{child_link_text} {child_href}"
                        child_link_score = score_text(child_combined)

                        if child_link_score >= 6 and has_health_term(child_combined):
                            save_opportunity(
                                supabase=supabase,
                                source=source,
                                url=child_href,
                                title=child_link_text or child_href,
                                description=child_link_text,
                                raw_text=child_combined
                            )
                            saved_count += 1
                            total_saved += 1
                            print(
                                f"Saved child link score={child_link_score}: "
                                f"{child_link_text or child_href}"
                            )

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
                f"Finished {state} — saved {saved_count}, "
                f"followed {followed_count}, skipped {skipped_count}"
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
    print(f"Total opportunities saved: {total_saved}")
    print(f"Total source errors: {total_errors}")


if __name__ == "__main__":
    run_scraper()
