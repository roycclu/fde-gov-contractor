import os
from datetime import datetime

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

app = FastAPI(title="GovTrack — Federal Procurement Intelligence")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

EXA_API_KEY = os.getenv("EXA_API_KEY", "")
EXA_BASE = "https://api.exa.ai"

GOV_DOMAINS = [
    "sam.gov",
    "usaspending.gov",
    "govconwire.com",
    "nextgov.com",
    "defensenews.com",
    "fedscoop.com",
    "federalnewsnetwork.com",
    "fcw.com",
    "govinfo.gov",
    "acquisition.gov",
    "bloomberg.com",
    "reuters.com",
    "politico.com",
    "rollcall.com",
]


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("govtrack.html", {"request": request})


@app.get("/govtrack")
async def govtrack_redirect():
    return RedirectResponse("/")


@app.get("/brief")
async def brief(request: Request):
    return templates.TemplateResponse("brief.html", {"request": request})


# ─── Helpers ─────────────────────────────────────────────────────────────────

def fmt_date(raw: str) -> str:
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return raw[:10] if len(raw) >= 10 else raw


def classify(result: dict) -> dict:
    url = result.get("url", "").lower()
    title = result.get("title", "").lower()

    if "sam.gov" in url:
        return {
            "tag": "New RFP",
            "tag_class": "rfp",
            "why": "Active procurement on SAM.gov — check set-aside type and submission deadline before anything else.",
        }
    if "usaspending.gov" in url:
        return {
            "tag": "Incumbent Intel",
            "tag_class": "incumbent",
            "why": "Award history exposes the incumbent contractor and total contract value — essential for competitive pricing.",
        }

    rfp_kws = {"rfp", "rfq", "solicitation", "sources sought", "bid opportunity", "request for proposal"}
    if any(kw in title for kw in rfp_kws):
        return {
            "tag": "New RFP",
            "tag_class": "rfp",
            "why": "New solicitation open — typical RFP windows are 30 days, start teaming conversations immediately.",
        }

    award_kws = {"awarded", "wins contract", "contract award", "prime contractor", "task order"}
    if any(kw in title for kw in award_kws):
        return {
            "tag": "Incumbent Intel",
            "tag_class": "incumbent",
            "why": "Incumbent identified — benchmark their past performance and price before the recompete window opens.",
        }

    return {
        "tag": "Agency News",
        "tag_class": "news",
        "why": "Agency budget and priority signals — align your capability statement to their stated strategic initiatives.",
    }


def build_summary(result: dict) -> str:
    highlights = result.get("highlights") or []
    if highlights:
        joined = " ".join(str(h) for h in highlights[:2])
        return joined[:320] + ("…" if len(joined) > 320 else "")
    text = result.get("text", "")
    return (text[:280] + "…") if len(text) > 280 else text or "No summary available."


async def exa_search(query: str, domains: list[str] | None, prefix: str) -> list:
    headers = {"x-api-key": EXA_API_KEY, "Content-Type": "application/json"}
    payload: dict = {
        "query": f"{prefix} {query}",
        "numResults": 7,
        "useAutoprompt": True,
        "contents": {
            "text": {"maxCharacters": 500},
            "highlights": {"numSentences": 2, "highlightsPerUrl": 1},
        },
    }
    if domains:
        payload["includeDomains"] = domains

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(f"{EXA_BASE}/search", headers=headers, json=payload)
        r.raise_for_status()
        results = r.json().get("results", [])

    if not results and domains:
        payload.pop("includeDomains", None)
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{EXA_BASE}/search", headers=headers, json=payload)
            r.raise_for_status()
            results = r.json().get("results", [])

    return results


# ─── Search API ──────────────────────────────────────────────────────────────

@app.post("/api/search")
async def search(request: Request):
    if not EXA_API_KEY:
        return JSONResponse(
            {"error": "EXA_API_KEY is not configured. Copy .env.example to .env and add your key."},
            status_code=500,
        )

    body = await request.json()
    query = (body.get("query") or "").strip()
    if not query:
        return JSONResponse({"error": "Query cannot be empty."}, status_code=400)

    try:
        raw = await exa_search(query, GOV_DOMAINS, "federal government contract procurement")
    except httpx.TimeoutException:
        return JSONResponse({"error": "Search timed out — please try again."}, status_code=504)
    except httpx.HTTPStatusError as exc:
        return JSONResponse(
            {"error": f"Exa API returned {exc.response.status_code}. Check your API key."},
            status_code=502,
        )
    except Exception as exc:
        return JSONResponse({"error": f"Unexpected error: {exc}"}, status_code=500)

    if not raw:
        return JSONResponse({"results": []})

    results = []
    for r in raw:
        c = classify(r)
        domain = ""
        try:
            from urllib.parse import urlparse
            domain = urlparse(r.get("url", "")).netloc.replace("www.", "")
        except Exception:
            pass

        results.append({
            "title": r.get("title") or "Untitled",
            "url": r.get("url", ""),
            "date": fmt_date(r.get("publishedDate", "")),
            "summary": build_summary(r),
            "tag": c["tag"],
            "tag_class": c["tag_class"],
            "why": c["why"],
            "domain": domain,
        })

    return JSONResponse({"results": results})
