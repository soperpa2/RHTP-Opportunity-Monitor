from fastapi import FastAPI, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
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
                background: linear-gradient(135deg, #163f4f, #2f7d6d);
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
                color: #163f4f;
                text-decoration: none;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="hero">
            <h1>RHTP Opportunity Monitor</h1>
            <p>State procurement, grant, and funding monitoring for Rural Health Transformation Program-related opportunities.</p>
            <div class="nav">
                <a href="/dashboard">Open Dashboard</a>
                <a href="/follow-up">Follow-Up Items</a>
                <a href="/archived">Archived Items</a>
                <a href="/not-relevant">Not Relevant Items</a>
                <a href="/sources">Sources JSON</a>
                <a href="/opportunities">Opportunities JSON</a>
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
        .order("first_seen_at", desc=True)
        .limit(250)
        .execute()
    )
    return result.data


def build_opportunity_card(item, show_unarchive=False, show_restore_relevant=False):
    opportunity_id = item.get("id")
    title = item.get("title") or "Untitled opportunity"
    url = item.get("url") or "#"
    state = item.get("state") or "Unknown"
    agency = item.get("agency") or ""
    description = item.get("description") or ""
    first_seen = item.get("first_seen_at") or ""
    last_seen = item.get("last_seen_at") or ""
    review_status = item.get("review_status") or "new"
    follow_up = item.get("follow_up")

    follow_badge = ""
    if follow_up:
        follow_badge = "<span class='badge follow'>Follow-up</span>"

    restore_buttons = ""

    if show_unarchive:
        restore_buttons += f"""
        <form method="post" action="/opportunity/{opportunity_id}/unarchive">
            <button class="btn secondary" type="submit">Unarchive</button>
        </form>
        """

    if show_restore_relevant:
        restore_buttons += f"""
        <form method="post" action="/opportunity/{opportunity_id}/restore-relevant">
            <button class="btn secondary" type="submit">Restore to Dashboard</button>
        </form>
        """

    if not show_unarchive and not show_restore_relevant:
        action_buttons = f"""
        <form method="post" action="/opportunity/{opportunity_id}/follow-up">
            <button class="btn primary" type="submit">Save for Follow-Up</button>
        </form>
        <form method="post" action="/opportunity/{opportunity_id}/archive">
            <button class="btn secondary" type="submit">Archive</button>
        </form>
        <form method="post" action="/opportunity/{opportunity_id}/not-relevant">
            <button class="btn danger" type="submit">Not Relevant</button>
        </form>
        """
    else:
        action_buttons = restore_buttons

    return f"""
    <div class="card">
        <div class="card-top">
            <span class="state">{state}</span>
            <span class="badge status">{review_status}</span>
            {follow_badge}
        </div>
        <h3>{title[:180]}</h3>
        <p class="agency">{agency}</p>
        <p>{description[:320]}</p>

        <div class="meta">
            <div><strong>First seen:</strong> {first_seen[:10]}</div>
            <div><strong>Last seen:</strong> {last_seen[:10]}</div>
        </div>

        <div class="card-footer">
            <a href="{url}" target="_blank">Open source →</a>
        </div>

        <div class="actions">
            {action_buttons}
        </div>
    </div>
    """


def page_shell(title, subtitle, content, active="dashboard"):
    return f"""
    <html>
    <head>
        <title>{title}</title>
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
                padding: 34px 46px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 34px;
                letter-spacing: -0.5px;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 16px;
                max-width: 950px;
                opacity: 0.95;
                line-height: 1.5;
            }}
            .nav {{
                margin-top: 22px;
            }}
            .nav a {{
                display: inline-block;
                margin-right: 10px;
                margin-bottom: 8px;
                padding: 9px 12px;
                border-radius: 999px;
                background: rgba(255,255,255,0.18);
                color: white;
                text-decoration: none;
                font-weight: 700;
                font-size: 13px;
            }}
            .nav a.active {{
                background: white;
                color: #163f4f;
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
            form.filter-form {{
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
            input, textarea {{
                width: 100%;
                padding: 11px 12px;
                border-radius: 10px;
                border: 1px solid #cfd8dc;
                font-size: 14px;
            }}
            button, .clear {{
                padding: 10px 12px;
                border-radius: 10px;
                border: none;
                color: white;
                font-weight: 700;
                cursor: pointer;
                text-decoration: none;
                text-align: center;
                font-size: 13px;
            }}
            .btn.primary, button.primary {{
                background: #2f7d6d;
            }}
            .btn.secondary, button.secondary {{
                background: #536878;
            }}
            .btn.danger, button.danger {{
                background: #a33a3a;
            }}
            .clear {{
                background: #6b7280;
                display: inline-block;
                padding: 11px 14px;
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
                grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
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
                min-height: 285px;
            }}
            .card-top {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
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
            .status {{
                background: #edf2f7;
                color: #374151;
            }}
            .follow {{
                background: #dff7ec;
                color: #166534;
            }}
            .card h3 {{
                margin: 0 0 8px 0;
                font-size: 17px;
                line-height: 1.35;
                color: #111827;
            }}
            .agency {{
                font-size: 13px;
                color: #6b7280;
                margin: 0 0 10px 0;
                font-weight: 700;
            }}
            .card p {{
                color: #4b5563;
                font-size: 14px;
                line-height: 1.45;
                margin: 0 0 14px 0;
            }}
            .meta {{
                background: #f8fafc;
                border: 1px solid #edf2f7;
                padding: 10px;
                border-radius: 10px;
                font-size: 12px;
                color: #4b5563;
                margin-top: auto;
                margin-bottom: 12px;
            }}
            .card-footer {{
                border-top: 1px solid #e5e7eb;
                padding-top: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 13px;
                color: #6b7280;
                margin-bottom: 12px;
            }}
            .card-footer a {{
                color: #2f7d6d;
                font-weight: 700;
                text-decoration: none;
            }}
            .actions {{
                display: grid;
                grid-template-columns: 1fr;
                gap: 8px;
            }}
            .actions form {{
                margin: 0;
            }}
            .actions button {{
                width: 100%;
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
            <h1>{title}</h1>
            <p>{subtitle}</p>
            <div class="nav">
                <a class="{'active' if active == 'dashboard' else ''}" href="/dashboard">Dashboard</a>
                <a class="{'active' if active == 'follow-up' else ''}" href="/follow-up">Follow-Up</a>
                <a class="{'active' if active == 'archived' else ''}" href="/archived">Archived</a>
                <a class="{'active' if active == 'not-relevant' else ''}" href="/not-relevant">Not Relevant</a>
                <a href="/sources">Sources JSON</a>
                <a href="/opportunities">Opportunities JSON</a>
            </div>
        </div>
        <div class="container">
            {content}
        </div>
    </body>
    </html>
    """


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    state: str = Query(default=""),
    keyword: str = Query(default="")
):
    supabase = get_supabase()

    result = (
        supabase
        .table("raw_opportunities")
        .select("*")
        .eq("archived", False)
        .eq("not_relevant", False)
        .order("first_seen_at", desc=True)
        .limit(250)
        .execute()
    )

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
    follow_up_count = len([item for item in opportunities if item.get("follow_up")])
    states_count = len(set([item.get("state") for item in opportunities if item.get("state")]))

    cards = "".join([build_opportunity_card(item) for item in opportunities])

    if not cards:
        cards = """
        <div class="empty">
            <h3>No actionable opportunities found</h3>
            <p>Try clearing filters or rerun the scraper. Archived and not-relevant items are hidden from this view.</p>
        </div>
        """

    content = f"""
        <div class="metrics">
            <div class="metric">
                <div class="metric-label">Actionable Opportunities</div>
                <div class="metric-value">{total_count}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Saved for Follow-Up</div>
                <div class="metric-value">{follow_up_count}</div>
            </div>
            <div class="metric">
                <div class="metric-label">States Represented</div>
                <div class="metric-value">{states_count}</div>
            </div>
        </div>

        <div class="filters">
            <form class="filter-form" method="get" action="/dashboard">
                <div>
                    <label>Filter by State</label>
                    <input name="state" placeholder="Example: Maryland" value="{state}">
                </div>
                <div>
                    <label>Filter by Keyword</label>
                    <input name="keyword" placeholder="Example: RHTP, RFA, grant" value="{keyword}">
                </div>
                <div>
                    <button class="primary" type="submit">Apply Filters</button>
                </div>
                <div>
                    <a class="clear" href="/dashboard">Clear Filters</a>
                </div>
            </form>
        </div>

        <div class="section-title">
            <h2>Actionable RHTP Opportunities</h2>
        </div>

        <div class="grid">
            {cards}
        </div>

        <p class="small-note">
            This view hides archived and not-relevant items. The scraper updates last_seen_at for previously known URLs without redisplaying duplicates.
        </p>
    """

    return page_shell(
        title="RHTP Opportunity Dashboard",
        subtitle="Actionable procurement, grant, RFA, RFP, NOFO, and funding opportunity signals related to the Rural Health Transformation Program.",
        content=content,
        active="dashboard"
    )


@app.get("/follow-up", response_class=HTMLResponse)
def follow_up():
    supabase = get_supabase()
    result = (
        supabase
        .table("raw_opportunities")
        .select("*")
        .eq("follow_up", True)
        .eq("archived", False)
        .eq("not_relevant", False)
        .order("first_seen_at", desc=True)
        .limit(250)
        .execute()
    )

    opportunities = result.data or []
    cards = "".join([build_opportunity_card(item) for item in opportunities])

    if not cards:
        cards = """
        <div class="empty">
            <h3>No follow-up items yet</h3>
            <p>Use “Save for Follow-Up” on the dashboard to add items here.</p>
        </div>
        """

    content = f"""
        <div class="section-title">
            <h2>Saved for Follow-Up</h2>
        </div>
        <div class="grid">{cards}</div>
    """

    return page_shell(
        title="Follow-Up Opportunities",
        subtitle="Opportunities saved for business development, review, or outreach.",
        content=content,
        active="follow-up"
    )


@app.get("/archived", response_class=HTMLResponse)
def archived():
    supabase = get_supabase()
    result = (
        supabase
        .table("raw_opportunities")
        .select("*")
        .eq("archived", True)
        .order("first_seen_at", desc=True)
        .limit(250)
        .execute()
    )

    opportunities = result.data or []
    cards = "".join([
        build_opportunity_card(item, show_unarchive=True)
        for item in opportunities
    ])

    if not cards:
        cards = """
        <div class="empty">
            <h3>No archived opportunities</h3>
            <p>Archived items will appear here and can be restored if needed.</p>
        </div>
        """

    content = f"""
        <div class="section-title">
            <h2>Archived Opportunities</h2>
        </div>
        <div class="grid">{cards}</div>
    """

    return page_shell(
        title="Archived Opportunities",
        subtitle="Opportunities that no longer require active follow-up. You can unarchive them if needed.",
        content=content,
        active="archived"
    )


@app.get("/not-relevant", response_class=HTMLResponse)
def not_relevant():
    supabase = get_supabase()
    result = (
        supabase
        .table("raw_opportunities")
        .select("*")
        .eq("not_relevant", True)
        .order("first_seen_at", desc=True)
        .limit(250)
        .execute()
    )

    opportunities = result.data or []
    cards = "".join([
        build_opportunity_card(item, show_restore_relevant=True)
        for item in opportunities
    ])

    if not cards:
        cards = """
        <div class="empty">
            <h3>No not-relevant items</h3>
            <p>Items marked not relevant will appear here and can be restored if needed.</p>
        </div>
        """

    content = f"""
        <div class="section-title">
            <h2>Not Relevant Items</h2>
        </div>
        <div class="grid">{cards}</div>
    """

    return page_shell(
        title="Not Relevant Items",
        subtitle="Items removed from the dashboard because they are not relevant to RHTP opportunity monitoring.",
        content=content,
        active="not-relevant"
    )


@app.post("/opportunity/{opportunity_id}/follow-up")
def mark_follow_up(opportunity_id: str):
    supabase = get_supabase()
    supabase.table("raw_opportunities").update({
        "follow_up": True,
        "review_status": "follow_up"
    }).eq("id", opportunity_id).execute()
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/opportunity/{opportunity_id}/archive")
def archive_opportunity(opportunity_id: str):
    supabase = get_supabase()
    supabase.table("raw_opportunities").update({
        "archived": True,
        "review_status": "archived"
    }).eq("id", opportunity_id).execute()
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/opportunity/{opportunity_id}/not-relevant")
def mark_not_relevant(opportunity_id: str):
    supabase = get_supabase()
    supabase.table("raw_opportunities").update({
        "not_relevant": True,
        "review_status": "not_relevant"
    }).eq("id", opportunity_id).execute()
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/opportunity/{opportunity_id}/unarchive")
def unarchive_opportunity(opportunity_id: str):
    supabase = get_supabase()
    supabase.table("raw_opportunities").update({
        "archived": False,
        "review_status": "follow_up",
        "follow_up": True
    }).eq("id", opportunity_id).execute()
    return RedirectResponse(url="/archived", status_code=303)


@app.post("/opportunity/{opportunity_id}/restore-relevant")
def restore_relevant(opportunity_id: str):
    supabase = get_supabase()
    supabase.table("raw_opportunities").update({
        "not_relevant": False,
        "review_status": "new"
    }).eq("id", opportunity_id).execute()
    return RedirectResponse(url="/not-relevant", status_code=303)
