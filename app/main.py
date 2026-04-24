from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from app.database import get_supabase

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>RHTP Opportunity Monitor</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f7fa;
                margin: 0;
                padding: 40px;
                color: #1f2937;
            }
            .hero {
                background: linear-gradient(135deg, #1f4e5f, #2f7d6d);
                color: white;
                padding: 36px;
                border-radius: 18px;
                margin-bottom: 28px;
            }
            .hero h1 {
                margin: 0 0 10px 0;
                font-size: 34px;
            }
            .hero p {
                margin: 0;
                font-size: 17px;
                opacity: 0.95;
            }
            .nav a {
                display: inline-block;
                margin-right: 12px;
                margin-top: 20px;
                padding: 10px 14px;
                border-radius: 8px;
                background: white;
                color: #1f4e5f;
                text-decoration: none;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="hero">
            <h1>RHTP Opportunity Monitor</h1>
            <p>State procurement monitoring for Rural Health Transformation Program-related opportunities.</p>
            <div class="nav">
                <a href="/dashboard">Open Dashboard</a>
                <a href="/sources">View Sources JSON</a>
                <a href="/opportunities">View Opportunities JSON</a>
                <a href="/health">Health Check</a>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/sources")
def sources():
    supabase = get_supabase()
    result = supabase.table("sources").select("*").order("state").execute()
    return result.data


@app.get("/opportunities")
def opportunities():
    supabase = get_supabase()
    result = (
        supabase
        .table("raw_opportunities")
        .select("*")
        .order("ingested_at", desc=True)
        .limit(100)
        .execute()
    )
    return result.data


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    state: str = Query(default=""),
    keyword: str = Query(default="")
):
    supabase = get_supabase()

    query = (
        supabase
        .table("raw_opportunities")
        .select("*")
        .order("ingested_at", desc=True)
        .limit(250)
    )

    result = query.execute()
    opportunities = result.data or []

    if state:
        opportunities = [
            item for item in opportunities
            if (item.get("state") or "").lower() == state.lower()
        ]

    if keyword:
        opportunities = [
            item for item in opportunities
            if keyword.lower() in (
                (item.get("title") or "") + " " +
                (item.get("description") or "") + " " +
                (item.get("raw_text") or "")
            ).lower()
        ]

    total_count = len(opportunities)
    states_count = len(set([item.get("state") for item in opportunities if item.get("state")]))

    high_value_terms = [
        "rural health",
        "rhtp",
        "medicaid",
        "telehealth",
        "behavioral health",
        "care coordination",
        "interoperability",
        "health workforce",
        "remote patient monitoring",
        "fqhc"
    ]

    high_value_count = 0
    cards = ""

    for item in opportunities:
        title = item.get("title") or "Untitled opportunity"
        url = item.get("url") or "#"
        item_state = item.get("state") or "Unknown"
        description = item.get("description") or ""
        ingested = item.get("ingested_at") or ""

        combined = f"{title} {description} {item.get('raw_text') or ''}".lower()
        matched_terms = [term for term in high_value_terms if term in combined]

        if matched_terms:
            high_value_count += 1
            badge = "High relevance"
            badge_class = "badge high"
        else:
            badge = "Needs review"
            badge_class = "badge medium"

        match_html = ""
        if matched_terms:
            match_html = "".join([f"<span class='tag'>{term}</span>" for term in matched_terms[:5]])
        else:
            match_html = "<span class='tag muted'>general procurement signal</span>"

        cards += f"""
        <div class="card">
            <div class="card-top">
                <span class="state">{item_state}</span>
                <span class="{badge_class}">{badge}</span>
            </div>
            <h3>{title[:160]}</h3>
            <p>{description[:260]}</p>
            <div class="tags">
                {match_html}
            </div>
            <div class="card-footer">
                <span>{ingested[:10]}</span>
                <a href="{url}" target="_blank">Open source →</a>
            </div>
        </div>
        """

    if not cards:
        cards = """
        <div class="empty">
            <h3>No matching opportunities found</h3>
            <p>Try clearing the state or keyword filters.</p>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>RHTP Opportunity Dashboard</title>
        <style>
            * {{
                box-sizing: border-box;
            }}
            body {{
                margin: 0;
                font-family: Arial, Helvetica, sans-serif;
                background: #f3f6f8;
                color: #1f2937;
            }}
            .header {{
                background: linear-gradient(135deg, #163f4f, #2f7d6d);
                color: white;
                padding: 38px 46px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 34px;
                letter-spacing: -0.5px;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 16px;
                max-width: 900px;
                opacity: 0.95;
                line-height: 1.5;
            }}
            .container {{
                padding: 28px 46px 46px 46px;
            }}
            .metrics {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 18px;
                margin-bottom: 24px;
            }}
            .metric {{
                background: white;
                padding: 22px;
                border-radius: 16px;
                box-shadow: 0 8px 22px rgba(31, 41, 55, 0.08);
                border: 1px solid #e5e7eb;
            }}
            .metric-label {{
                font-size: 13px;
                color: #6b7280;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            .metric-value {{
                font-size: 32px;
                font-weight: 700;
                color: #163f4f;
            }}
            .filters {{
                background: white;
                padding: 20px;
                border-radius: 16px;
                margin-bottom: 24px;
                box-shadow: 0 8px 22px rgba(31, 41, 55, 0.08);
                border: 1px solid #e5e7eb;
            }}
            form {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 14px;
                align-items: end;
            }}
            label {{
                display: block;
                font-size: 13px;
                font-weight: 700;
                margin-bottom: 6px;
                color: #374151;
            }}
            input {{
                width: 100%;
                padding: 11px 12px;
                border-radius: 10px;
                border: 1px solid #cfd8dc;
                font-size: 14px;
            }}
            button, .clear {{
                padding: 11px 14px;
                border-radius: 10px;
                border: none;
                background: #2f7d6d;
                color: white;
                font-weight: 700;
                cursor: pointer;
                text-decoration: none;
                text-align: center;
                font-size: 14px;
            }}
            .clear {{
                background: #6b7280;
                display: inline-block;
            }}
            .section-title {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin: 18px 0;
            }}
            .section-title h2 {{
                margin: 0;
                font-size: 22px;
                color: #1f2937;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
                gap: 18px;
            }}
            .card {{
                background: white;
                border-radius: 16px;
                padding: 20px;
                box-shadow: 0 8px 22px rgba(31, 41, 55, 0.08);
                border: 1px solid #e5e7eb;
                display: flex;
                flex-direction: column;
                min-height: 245px;
            }}
            .card-top {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }}
            .state {{
                font-size: 13px;
                font-weight: 700;
                color: #163f4f;
                background: #e8f3f1;
                padding: 6px 9px;
                border-radius: 999px;
            }}
            .badge {{
                font-size: 12px;
                padding: 6px 9px;
                border-radius: 999px;
                font-weight: 700;
            }}
            .high {{
                background: #dff7ec;
                color: #166534;
            }}
            .medium {{
                background: #fff4d6;
                color: #92400e;
            }}
            .card h3 {{
                margin: 0 0 10px 0;
                font-size: 17px;
                line-height: 1.35;
                color: #111827;
            }}
            .card p {{
                color: #4b5563;
                font-size: 14px;
                line-height: 1.45;
                margin: 0 0 14px 0;
            }}
            .tags {{
                margin-top: auto;
                margin-bottom: 16px;
            }}
            .tag {{
                display: inline-block;
                font-size: 12px;
                background: #edf2f7;
                color: #374151;
                padding: 5px 8px;
                border-radius: 999px;
                margin: 3px 4px 3px 0;
            }}
            .muted {{
                color: #6b7280;
            }}
            .card-footer {{
                border-top: 1px solid #e5e7eb;
                padding-top: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 13px;
                color: #6b7280;
            }}
            .card-footer a {{
                color: #2f7d6d;
                font-weight: 700;
                text-decoration: none;
            }}
            .empty {{
                background: white;
                padding: 28px;
                border-radius: 16px;
                box-shadow: 0 8px 22px rgba(31, 41, 55, 0.08);
                border: 1px solid #e5e7eb;
            }}
            .small-note {{
                color: #6b7280;
                font-size: 13px;
                margin-top: 22px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>RHTP Opportunity Dashboard</h1>
            <p>
                Monitoring state procurement sources for Rural Health Transformation Program,
                Medicaid, telehealth, behavioral health, workforce, interoperability, and related opportunities.
            </p>
        </div>

        <div class="container">
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">Displayed Records</div>
                    <div class="metric-value">{total_count}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">States Represented</div>
                    <div class="metric-value">{states_count}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">High-Relevance Signals</div>
                    <div class="metric-value">{high_value_count}</div>
                </div>
            </div>

            <div class="filters">
                <form method="get" action="/dashboard">
                    <div>
                        <label>Filter by State</label>
                        <input name="state" placeholder="Example: Texas" value="{state}">
                    </div>
                    <div>
                        <label>Filter by Keyword</label>
                        <input name="keyword" placeholder="Example: Medicaid, telehealth, rural" value="{keyword}">
                    </div>
                    <div>
                        <button type="submit">Apply Filters</button>
                    </div>
                    <div>
                        <a class="clear" href="/dashboard">Clear Filters</a>
                    </div>
                </form>
            </div>

            <div class="section-title">
                <h2>Recent Opportunity Signals</h2>
            </div>

            <div class="grid">
                {cards}
            </div>

            <p class="small-note">
                This dashboard displays scraped procurement signals. Use source links to verify opportunity details,
                deadlines, eligibility, and procurement requirements directly on the official state site.
            </p>
        </div>
    </body>
    </html>
    """
