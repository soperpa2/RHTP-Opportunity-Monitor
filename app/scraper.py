OPPORTUNITY_TERMS = [
    "grant opportunity", "funding opportunity", "notice of funding", "nofo",
    "request for proposals", "request for applications",
    "rfp", "rfa", "rfi", "rfq",
    "solicitation", "bid opportunity", "contract opportunity",
    "procurement opportunity", "application deadline",
    "applications due", "apply now", "open opportunity"
]

RHTP_HEALTH_TERMS = [
    "rural health transformation", "rhtp", "rural health",
    "medicaid", "rural hospital", "fqhc",
    "telehealth", "behavioral health", "care coordination",
    "remote patient monitoring", "health workforce",
    "population health", "interoperability"
]

EXCLUDE_TERMS = [
    "mailto:", "tel:", "contact us", "staff directory",
    "newsletter", "calendar", "training", "webinar",
    "press release", "annual report",
    "construction", "janitorial", "landscaping",
    "hvac", "vehicle", "office supplies"
]


def normalize(text):
    return (text or "").lower().strip()


def count_matches(text, terms):
    text = normalize(text)
    return sum(1 for term in terms if term in text)


def is_relevant_opportunity(text):
    text = normalize(text)

    opportunity_score = count_matches(text, OPPORTUNITY_TERMS)
    health_score = count_matches(text, RHTP_HEALTH_TERMS)
    exclude_score = count_matches(text, EXCLUDE_TERMS)

    if exclude_score > 0:
        return False, opportunity_score, health_score

    if opportunity_score >= 1 and health_score >= 1:
        return True, opportunity_score, health_score

    return False, opportunity_score, health_score
