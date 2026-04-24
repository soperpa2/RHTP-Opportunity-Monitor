import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
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

    print(f"TEST_MODE={test_mode}")
    print(f"MAX_SOURCES={max_sources}")

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

    for source in sources:
        state = source.get("state")
        url = source.get("url")
        source_id = source.get("id")

        print(f"\nCrawling {state}: {url}")

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=25
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text(" ", strip=True)
            links = soup.find_all("a", href=True)

            saved_count = 0
            skipped_count = 0

            source_page_score = score_text(page_text)

            if source_page_score >= 6 and has_health_term(page_text):
                opportunity = {
                    "source_id": source_id,
                    "state": state,
                    "agency": source.get("agency", "State Agency"),
                    "title": source.get("page_name") or f"{state} relevant source page",
                    "url": url,
                    "description": page_text[:500],
                    "raw_text": page_text[:2000]
                }

                supabase.table("raw_opportunities").upsert(
                    opportunity,
                    on_conflict="url"
                ).execute()

                saved_count += 1
                total_saved += 1
                print(f"Saved source page score={source_page_score}: {opportunity['title']}")

            for link in links:
                link_text = link.get_text(" ", strip=True)
                href = urljoin(url, link["href"])

                combined_text = f"{link_text} {href}"
                score = score_text(combined_text)

                if score >= 6 and has_health_term(combined_text):
                    opportunity = {
                        "source_id": source_id,
                        "state": state,
                        "agency": source.get("agency", "State Agency"),
                        "title": link_text[:200] if link_text else href[:200],
                        "url": href,
                        "description": link_text[:500] if link_text else "",
                        "raw_text": combined_text[:2000]
                    }

                    supabase.table("raw_opportunities").upsert(
                        opportunity,
                        on_conflict="url"
                    ).execute()

                    saved_count += 1
                    total_saved += 1
                    print(f"Saved link score={score}: {opportunity['title']}")
                else:
                    skipped_count += 1

            update_source_status(
                supabase,
                source_id=source_id,
                status="success",
                error=None,
                successful=True
            )

            print(f"Finished {state} — saved {saved_count}, skipped {skipped_count}")

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
