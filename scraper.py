from __future__ import annotations
from dataclasses import dataclass
import json
import re
from pathlib import Path

@dataclass
class ScoreResult:
    matched_keywords: list[str]
    matched_phrases: list[str]
    excluded_terms: list[str]
    relevance_score: int
    strategic_fit_score: int
    include_for_review: str
    explanation: str

def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s\-/]", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def load_keywords(path: str | Path = "data/keywords.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _contains_phrase(text: str, phrase: str) -> bool:
    return normalize_text(phrase) in text

def score_opportunity(title: str, description: str = "", keywords_config: dict | None = None) -> ScoreResult:
    config = keywords_config or load_keywords()
    text = normalize_text(f"{title} {description}")
    matched_phrases = [p for p in config.get("high_priority_phrases", []) if _contains_phrase(text, p)]
    matched_keywords = []
    for k in config.get("keywords", []):
        token = normalize_text(k)
        if re.search(rf"\b{re.escape(token)}\b", text):
            matched_keywords.append(k)
    excluded_terms = [e for e in config.get("exclude_terms", []) if _contains_phrase(text, e)]

    score = len(matched_phrases) * 3 + len(matched_keywords)
    score -= len(excluded_terms) * 3

    strategic_terms = ["medicaid", "rural", "interoperability", "telehealth", "workforce", "care coordination", "population health", "fqhc"]
    strategic_fit = sum(1 for t in strategic_terms if normalize_text(t) in text)

    if score >= 3:
        include = "yes"
    elif score >= 1:
        include = "maybe"
    else:
        include = "no"

    explanation = f"{len(matched_phrases)} phrase matches, {len(matched_keywords)} keyword matches, {len(excluded_terms)} exclusions."
    return ScoreResult(matched_keywords, matched_phrases, excluded_terms, score, strategic_fit, include, explanation)
