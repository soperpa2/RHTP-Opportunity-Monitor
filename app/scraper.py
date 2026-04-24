import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.database import get_supabase


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

OPPORTUNITY_TERMS = [
    "grant opportunity",
    "funding opportunity",
    "notice of funding",
    "nofo",
    "request for proposals",
    "request for applications",
    "request for information",
    "request for qualifications",
    "rfp",
    "rfa",
    "rfi",
    "rfq",
    "solicitation",
    "bid opportunity",
    "contract opportunity",
    "procurement opportunity",
    "application deadline",
    "applications due",
    "apply now",
    "open opportunity",
    "current opportunities",
    "funding available",
    "grant application",
    "competitive grant",
    "letter of interest",
    "loi",
    "application portal",
    "submit application"
]

RHTP_HEALTH_TERMS = [
    "rural health transformation",
    "rural health transformation program",
    "rhtp",
    "rural health",
    "medicaid",
    "medicaid transformation",
    "rural hospital",
    "fqhc",
    "federally qualified health center",
    "telehealth",
    "telemedicine",
    "behavioral health",
    "mental health",
    "care coordination",
    "remote patient monitoring",
    "mobile health",
    "food as medicine",
    "health workforce",
    "community health worker",
    "population health",
    "public health",
    "health information exchange",
    "interoperability",
    "maternal health",
    "substance use",
    "opioid",
    "primary care",
    "rural provider",
    "rural community"
]

FOLLOW_LINK_TERMS = [
    "rural health transformation",
    "rhtp",
    "grant",
    "funding",
    "opportunity",
    "opportunities",
    "procurement",
    "solicitation",
    "rfp",
    "rfa",
    "rfi",
    "rfq",
    "bid",
    "contract",
    "application",
    "apply",
    "notice",
    "medicaid"
]

EXCLUDE_TERMS = [
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


def count_matches(text, terms):
    text = normalize(text)
    return sum(1 for term in terms if term in text)


def is_excluded(text):
    return count_matches(text, EXCLUDE_TERMS) > 0


def is_relevant_opportunity(text):
    text = normalize(text)

    if is_excluded(text):
        return False, 0, 0

    opportunity_score = count_matches(text, OPPORTUNITY_TERMS)
    health_score = count_matches(text, RHTP_HEALTH_TERMS)

    if opportunity_score >= 1 and health_score >= 1:
        return True, opportunity_score, health_score

    return False, opportunity_score, health_score


def should_follow_link(link_text, href):
    combined = normalize(f"{link_text} {href}")

    if is_excluded(combined):
        return False

    return count_matches(combined, FOLLOW_LINK_TERMS) > 0


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

        if "mailto:" in href.lower() or "tel:" in href.lower():
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
    raw_text,
    opportunity_score,
    health_score
):
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

    print(
        f"Saved opportunity_score={opportunity_score}, "
        f"health_score={health_score}: {opportunity['title']}"
    )


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
            followed_count = 0
            skipped_count = 0

            is_match, opportunity_score, health_score = is_relevant_opportunity(page_text)

            if is_match:
                save_opportunity(
                    supabase=supabase,
                    source=source,
                    url=url,
                    title=source.get("page_name") or f"{state} opportunity source page",
                    description=page_text,
                    raw_text=page_text,
                    opportunity_score=opportunity_score,
                    health_score=health_score
                )
                saved_count += 1
                total_saved += 1

            candidate_links = []

            for link in links:
                link_text = link["text"]
                href = link["url"]
                combined_text = f"{link_text} {href}"

                is_match, opportunity_score, health_score = is_relevant_opportunity(combined_text)

                if is_match:
                    save_opportunity(
                        supabase=supabase,
                        source=source,
                        url=href,
                        title=link_text or href,
                        description=link_text,
                        raw_text=combined_text,
                        opportunity_score=opportunity_score,
                        health_score=health_score
                    )
                    saved_count += 1
                    total_saved += 1

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

                    is_match, opportunity_score, health_score = is_relevant_opportunity(child_text)

                    if is_match:
                        save_opportunity(
                            supabase=supabase,
                            source=source,
                            url=follow_url,
                            title=link["text"] or follow_url,
                            description=child_text,
                            raw_text=child_text,
                            opportunity_score=opportunity_score,
                            health_score=health_score
                        )
                        saved_count += 1
                        total_saved += 1

                    for child_link in child_links:
                        child_link_text = child_link["text"]
                        child_href = child_link["url"]
                        child_combined = f"{child_link_text} {child_href}"

                        is_match, opportunity_score, health_score = is_relevant_opportunity(
                            child_combined
                        )

                        if is_match:
                            save_opportunity(
                                supabase=supabase,
                                source=source,
                                url=child_href,
                                title=child_link_text or child_href,
                                description=child_link_text,
                                raw_text=child_combined,
                                opportunity_score=opportunity_score,
                                health_score=health_score
                            )
                            saved_count += 1
                            total_saved += 1

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
