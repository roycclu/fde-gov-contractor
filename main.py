import os
from pathlib import Path
from datetime import datetime
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="ExaGov — Federal Procurement Intelligence")
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

EXA_API_KEY = os.getenv("EXA_API_KEY", "")
EXA_BASE = "https://api.exa.ai"

FEDERAL_PROCUREMENT_SITES = [
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

STATE_PROCUREMENT_SITES = [
    "california.bidsync.com",
    "procurement.opengov.com",
    "ogs.ny.gov",
    "mass.gov",
    "floridabidsystem.com",
    "bids.sciquest.com",
    "bidbuy.illinois.gov",
    "virginiamercury.com",
]

BUSINESS_TYPE_HINTS = {
    "IT and cybersecurity": [
        "zero trust",
        "cloud modernization",
        "cyber operations",
        "CMMC",
    ],
    "Logistics and supply chain": [
        "fleet maintenance",
        "warehousing",
        "distribution support",
        "transport operations",
    ],
    "Professional services and consulting": [
        "program management support",
        "advisory services",
        "management consulting",
    ],
    "Construction and facilities": [
        "facilities sustainment",
        "design-build",
        "infrastructure modernization",
    ],
    "Research and development": [
        "SBIR",
        "prototype development",
        "applied research",
    ],
    "Healthcare and life sciences": [
        "health IT",
        "clinical services",
        "biomedical research",
    ],
}

ALLOWED_SITES = set(FEDERAL_PROCUREMENT_SITES + STATE_PROCUREMENT_SITES)


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        request,
        "govtrack.html",
        {
            "federal_sites": FEDERAL_PROCUREMENT_SITES,
            "state_sites": STATE_PROCUREMENT_SITES,
            "business_types": list(BUSINESS_TYPE_HINTS.keys()),
            "business_type_hints": BUSINESS_TYPE_HINTS,
        },
    )


@app.get("/govtrack")
@app.get("/govtrack/", include_in_schema=False)
async def govtrack_redirect():
    return RedirectResponse("/")


@app.get("/brief")
@app.get("/brief/", include_in_schema=False)
@app.get("/market-brief", include_in_schema=False)
@app.get("/market-brief/", include_in_schema=False)
async def brief(request: Request):
    return templates.TemplateResponse(request, "brief.html", {})


@app.get("/saved")
@app.get("/saved/", include_in_schema=False)
async def saved_contracts(request: Request):
    return templates.TemplateResponse(request, "saved.html", {})


# ─── Helpers ─────────────────────────────────────────────────────────────────

def fmt_date(raw: str) -> str:
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return raw[:10] if len(raw) >= 10 else raw


def date_sort_key(raw: str) -> float:
    if not raw:
        return 0.0
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


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


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def normalize_selected_domains(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return FEDERAL_PROCUREMENT_SITES
    cleaned = []
    for item in raw:
        if not isinstance(item, str):
            continue
        domain = item.strip().lower()
        if domain and domain in ALLOWED_SITES:
            cleaned.append(domain)
    cleaned = dedupe_keep_order(cleaned)
    return cleaned or FEDERAL_PROCUREMENT_SITES


def normalize_business_types(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    allowed = set(BUSINESS_TYPE_HINTS.keys())
    return [item for item in raw if isinstance(item, str) and item in allowed]


def normalize_additional_queries(raw: Any) -> list[str]:
    if isinstance(raw, str):
        candidates = [line.strip() for line in raw.splitlines()]
    elif isinstance(raw, list):
        candidates = [str(line).strip() for line in raw]
    else:
        candidates = []
    return [line for line in candidates if line]


async def exa_search(
    query: str,
    domains: list[str] | None,
    prefix: str,
    additional_queries: list[str] | None = None,
    start_published_date: str | None = None,
) -> list:
    headers = {"x-api-key": EXA_API_KEY, "Content-Type": "application/json"}
    payload: dict[str, Any] = {
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
    if additional_queries:
        payload["additionalQueries"] = additional_queries
    if start_published_date:
        payload["startPublishedDate"] = start_published_date

    async def post_search(run_payload: dict[str, Any]) -> list:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(f"{EXA_BASE}/search", headers=headers, json=run_payload)
            # Some Exa deployments may not support additionalQueries yet.
            if resp.status_code == 400 and "additionalQueries" in run_payload:
                fallback_payload = dict(run_payload)
                fallback_payload.pop("additionalQueries", None)
                resp = await client.post(f"{EXA_BASE}/search", headers=headers, json=fallback_payload)
            resp.raise_for_status()
            return resp.json().get("results", [])

    results = await post_search(payload)

    if not results and domains:
        fallback_payload = dict(payload)
        fallback_payload.pop("includeDomains", None)
        results = await post_search(fallback_payload)

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

    domains = normalize_selected_domains(body.get("selected_domains"))
    business_types = normalize_business_types(body.get("business_types"))
    additional_queries = normalize_additional_queries(body.get("additional_queries"))
    for business_type in business_types:
        additional_queries.extend(BUSINESS_TYPE_HINTS.get(business_type, []))
    additional_queries = dedupe_keep_order(additional_queries)

    raw_start_date = body.get("start_published_date") or None
    start_published_date: str | None = None
    if isinstance(raw_start_date, str) and raw_start_date:
        import re
        if re.match(r"^\d{4}-\d{2}-\d{2}", raw_start_date):
            start_published_date = raw_start_date

    try:
        raw = await exa_search(
            query=query,
            domains=domains,
            prefix="federal and state government contract procurement opportunities",
            additional_queries=additional_queries,
            start_published_date=start_published_date,
        )
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
        return JSONResponse({
            "results": [],
            "search_context": {
                "query": query,
                "include_domains": domains,
                "business_types": business_types,
                "additional_queries": additional_queries,
                "start_published_date": start_published_date,
            },
        })

    results = []
    for r in raw:
        c = classify(r)
        domain = ""
        raw_date = r.get("publishedDate", "")
        try:
            from urllib.parse import urlparse
            domain = urlparse(r.get("url", "")).netloc.replace("www.", "")
        except Exception:
            pass

        results.append({
            "title": r.get("title") or "Untitled",
            "url": r.get("url", ""),
            "date": fmt_date(raw_date),
            "raw_date": raw_date,
            "summary": build_summary(r),
            "highlights": r.get("highlights") or [],
            "source_excerpt": (r.get("text") or "")[:4000],
            "tag": c["tag"],
            "tag_class": c["tag_class"],
            "why": c["why"],
            "domain": domain,
        })

    results.sort(key=lambda item: date_sort_key(item.get("raw_date", "")), reverse=True)
    for item in results:
        item.pop("raw_date", None)

    return JSONResponse({
        "results": results,
        "search_context": {
            "query": query,
            "include_domains": domains,
            "business_types": business_types,
            "additional_queries": additional_queries,
            "start_published_date": start_published_date,
        },
    })
