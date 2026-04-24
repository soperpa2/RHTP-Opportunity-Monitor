import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.database import get_supabase

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

KEYWORDS = [
    "rfp",
    "rfi",
    "rfq",
    "bid",
    "bids",
    "solicitation",
    "solicitations",
    "procurement",
    "contract",
    "contracts",
    "opportunity",
    "opportunities",
    "vendor"
]

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

            for link in links:
                text = link.get_text(" ", strip=True)
                href = urljoin(source["url"], link["href"])

                combined_text = f"{text} {href}".lower()

                if any(keyword in combined_text for keyword in KEYWORDS):
                    opportunity = {
                        "source_id": source["id"],
                        "state": source["state"],
                        "agency": "State Procurement Office",
                        "title": text[:200] if text else href[:200],
                        "url": href,
                        "description": text[:500] if text else "",
                        "raw_text": combined_text[:2000]
                    }

                    supabase.table("raw_opportunities").upsert(
                        opportunity,
                        on_conflict="url"
                    ).execute()

                    saved_count += 1
                    print(f"Saved: {opportunity['title']}")

            print(f"Finished {source['state']} — saved {saved_count} links")

        except Exception as e:
            print("\n--- ERROR ---")
            print(f"State: {source.get('state')}")
            print(f"URL: {source.get('url')}")
            print(f"Error: {str(e)}")
            print("------------\n")
