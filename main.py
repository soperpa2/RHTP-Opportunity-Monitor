from __future__ import annotations
import argparse
from .database import init_schema
from .repository import create_crawl_run, finish_crawl_run, list_sources, seed_sources, upsert_opportunity
from .scraper import crawl_source

def run_crawl(limit: int | None = None) -> dict:
    sources = list_sources(active_only=True)
    if limit:
        sources = sources[:limit]
    run_id = create_crawl_run()
    pages_visited = 0
    found = 0
    errors: list[str] = []
    attempted = 0
    for source in sources:
        attempted += 1
        opps, visited, errs = crawl_source(source)
        pages_visited += visited
        errors.extend(errs)
        for opp in opps:
            upsert_opportunity(source, run_id, opp)
            found += 1
    finish_crawl_run(run_id, "completed_with_errors" if errors else "completed", attempted, pages_visited, found, errors)
    return {"run_id": run_id, "sources_attempted": attempted, "pages_visited": pages_visited, "opportunities_found": found, "errors": errors}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init-db", "seed", "crawl", "init-and-seed"])
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.command == "init-db":
        init_schema()
        print("Schema initialized.")
    elif args.command == "seed":
        print(f"Seeded {seed_sources()} sources.")
    elif args.command == "init-and-seed":
        init_schema()
        print(f"Seeded {seed_sources()} sources.")
    elif args.command == "crawl":
        print(run_crawl(limit=args.limit))

if __name__ == "__main__":
    main()
