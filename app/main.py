from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.database import get_supabase

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1>RHTP Opportunity Monitor</h1>
    <p>App is running.</p>
    <ul>
        <li><a href="/health">Health Check</a></li>
        <li><a href="/sources">Sources</a></li>
        <li><a href="/opportunities">Opportunities</a></li>
    </ul>
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
        .limit(50)
        .execute()
    )
    return result.data
