from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1>RHTP Opportunity Monitor</h1>
    <p>App is running</p>
    <ul>
        <li><a href="/health">Health Check</a></li>
    </ul>
    """
