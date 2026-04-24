from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any
from psycopg.types.json import Jsonb
from .database import fetch_all, fetch_one, get_conn
from .scorer import score_opportunity

def list_sources(active_only: bool = True) -> list[dict[str, Any]]:
    clause = "where active = true" if active_only else ""
    return fetch_all(f"select * from sources {clause} order by state")

def seed_sources(csv_path: str = "data/naspo_sources.csv") -> int:
    count = 0
    with open(csv_path, newline="", encoding="utf-8") as f, get_conn() as conn:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute(
                """
                insert into sources (
                    state, state_abbreviation, agency, agency_type, url, page_name, likely_content_type,
                    why_monitor_this, priority, notes, is_js_heavy_likely, requires_vendor_login_likely,
                    crawl_frequency, manual_verification_needed, source_priority, follow_links, max_links_to_follow, active
                ) values (
                    %(state)s, %(state_abbreviation)s, %(agency)s, %(agency_type)s, %(url)s, %(page_name)s, %(likely_content_type)s,
                    %(why_monitor_this)s, %(priority)s, %(notes)s, %(is_js_heavy_likely)s, %(requires_vendor_login_likely)s,
                    %(crawl_frequency)s, %(manual_verification_needed)s, %(source_priority)s, %(follow_links)s, %(max_links_to_follow)s, %(active)s
                )
                on conflict (url) do update set
                    state = excluded.state,
                    state_abbreviation = excluded.state_abbreviation,
                    updated_at = now()
                """,
                {
                    **row,
                    "source_priority": int(row.get("source_priority") or 1),
                    "max_links_to_follow": int(row.get("max_links_to_follow") or 10),
                    "active": str(row.get("active", "true")).lower() in ("true", "1", "yes"),
                },
            )
            count += 1
        conn.commit()
    return count

def create_crawl_run() -> str:
    row = fetch_one("insert into crawl_runs default values returning id")
    return str(row["id"])

def finish_crawl_run(run_id: str, status: str, sources_attempted: int, pages_visited: int, opportunities_found: int, errors: list[str]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            update crawl_runs
            set finished_at = now(), status = %s, sources_attempted = %s, pages_visited = %s,
                opportunities_found = %s, errors = %s
            where id = %s
            """,
            (status, sources_attempted, pages_visited, opportunities_found, Jsonb(errors), run_id),
        )
        conn.commit()

def upsert_opportunity(source: dict, run_id: str, opp) -> str:
    with get_conn() as conn:
        row = conn.execute(
            """
            insert into raw_opportunities (
                source_id, crawl_run_id, state, agency, title, url, description, raw_text, source_url, content_hash
            ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            on conflict (url) do update set
                title = excluded.title,
                description = excluded.description,
                raw_text = excluded.raw_text,
                content_hash = excluded.content_hash,
                last_seen_at = now()
            returning id
            """,
            (
                source["id"], run_id, source["state"], source.get("agency") or "State Procurement Office",
                opp.title, opp.url, opp.description, opp.raw_text, opp.source_url, opp.content_hash
            ),
        ).fetchone()
        opp_id = str(row["id"])
        result = score_opportunity(opp.title, opp.description)
        conn.execute(
            """
            insert into scored_opportunities (
                opportunity_id, matched_keywords, matched_phrases, excluded_terms, relevance_score,
                strategic_fit_score, include_for_review, explanation
            ) values (%s,%s,%s,%s,%s,%s,%s,%s)
            on conflict (opportunity_id) do update set
                matched_keywords = excluded.matched_keywords,
                matched_phrases = excluded.matched_phrases,
                excluded_terms = excluded.excluded_terms,
                relevance_score = excluded.relevance_score,
                strategic_fit_score = excluded.strategic_fit_score,
                include_for_review = excluded.include_for_review,
                explanation = excluded.explanation,
                created_at = now()
            """,
            (
                opp_id, result.matched_keywords, result.matched_phrases, result.excluded_terms,
                result.relevance_score, result.strategic_fit_score, result.include_for_review, result.explanation
            ),
        )
        conn.execute(
            "insert into review_pipeline (opportunity_id) values (%s) on conflict (opportunity_id) do nothing",
            (opp_id,),
        )
        conn.execute("update sources set last_crawled_at = now() where id = %s", (source["id"],))
        conn.commit()
        return opp_id

def dashboard_rows(include: str | None = None, state: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    where = []
    params: list[Any] = []
    if include:
        where.append("include_for_review = %s")
        params.append(include)
    if state:
        where.append("state = %s")
        params.append(state)
    clause = "where " + " and ".join(where) if where else ""
    params.append(limit)
    return fetch_all(f"select * from dashboard_opportunities {clause} order by relevance_score desc nulls last, first_seen_at desc limit %s", params)

def update_review(opportunity_id: str, review_status: str, pursue_status: str | None, notes: str | None) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            update review_pipeline
            set review_status=%s, pursue_status=%s, notes=%s, last_reviewed_at=now(), updated_at=now()
            where opportunity_id=%s
            """,
            (review_status, pursue_status, notes, opportunity_id),
        )
        conn.commit()

def stats() -> dict[str, Any]:
    return {
        "sources": fetch_one("select count(*) as n from sources")["n"],
        "opportunities": fetch_one("select count(*) as n from raw_opportunities")["n"],
        "high": fetch_one("select count(*) as n from scored_opportunities where include_for_review='yes'")["n"],
        "maybe": fetch_one("select count(*) as n from scored_opportunities where include_for_review='maybe'")["n"],
    }
