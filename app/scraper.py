import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.database import get_supabase

HEADERS = {"User-Agent": "RHTP Monitor"}

KEYWORDS = ["rfp", "rfi", "rfq", "bid", "solicitation", "procurement"]

def run_scraper():
    supabase = get_supabase()

    sources = supabase.table("sources").select("*").execute().data

    for source in sources:
        print(f"Crawling {source['state']}")

        try:
            response = requests.get(source["url"], headers=HEADERS, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")

            links = soup.find_all("a", href=True)

            for link in links:
                text = link.get_text(" ", strip=True).lower()
                href = urljoin(source["url"], link["href"])

                if any(k in text for k in KEYWORDS):
                    opportunity = {
                        "source_id": source["id"],
                        "state": source["state"],
                        "agency": "State Procurement Office",
                        "title": text[:200],
                        "url": href,
                        "description": text[:500],
                        "raw_text": text
                    }

                    supabase.table("raw_opportunities").upsert(
                        opportunity, on_conflict="url"
                    ).execute()

                    print(f"Saved: {text}")

        except Exception as e:
            print(f"Error in {source['state']}: {e}")
