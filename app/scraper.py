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
    "opioid"
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


def run_scraper():
    supabase = get_supabase()
    sources = supabase.table("sources").select("*").execute().data

    for source in sources:
        print(f"\nCrawling {source['state']}: {source['url']}")

        try:
            response = requests.get(
                source["url"],
                headers=HEADERS,
                timeout=20
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.find_all("a", href=True)

            saved_count = 0
            skipped_count = 0

            for link in links:
                link_text = link.get_text(" ", strip=True)
                href = urljoin(source["url"], link["href"])

                combined_text = f"{link_text} {href}"
                score = score_text(combined_text)

                if score >= 6 and has_health_term(combined_text):
                    opportunity = {
                        "source_id": source["id"],
                        "state": source["state"],
                        "agency": "State Procurement Office",
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
                    print(f"Saved score={score}: {opportunity['title']}")
                else:
                    skipped_count += 1

            print(
                f"Finished {source['state']} — saved {saved_count}, skipped {skipped_count}"
            )

        except Exception as e:
            print("\n--- ERROR ---")
            print(f"State: {source.get('state')}")
            print(f"URL: {source.get('url')}")
            print(f"Error: {str(e)}")
            print("------------\n")
