# ExaGov — Exa Market Intelligence Demo

An Exa-powered market intelligence app focused on **government contracting**.

## Live demos

| Route | Tool | Target user |
|---|---|---|
| `/` | ExaGov | Mid-market gov contractors |
| `/govtrack` | RFP Intelligence | Mid-market gov contractors |

---

## Setup

### 1. Clone / unzip the project

```bash
cd exa_gov_contractors
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> Python 3.11+ recommended.

### 3. Set your Exa API key

```bash
cp .env.example .env
# then edit .env and paste your key:
EXA_API_KEY=your_exa_api_key_here
```

Get a free API key at [exa.ai](https://exa.ai).

### 4. Run the server

```bash
uvicorn main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000).

---

## How it works

### GovTrack (`/govtrack`)
1. User types an agency + category (e.g. *"HHS cybersecurity"*).
2. Backend calls `POST https://api.exa.ai/search` with `includeDomains` targeting SAM.gov, USASpending.gov, and procurement news sites.
3. Results are classified into three tag types:
   - **New RFP** — live solicitations on SAM.gov or keyword-matched headlines
   - **Incumbent Intel** — USASpending award records, contract-award news
   - **Agency News** — budget signals, strategic priorities
4. Each card shows: title · 2-sentence highlight · date · *Why this matters* · source link.

The tool falls back to a broader (no-domain) Exa search if the targeted domains return zero results.

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `EXA_API_KEY` | **Yes** | Your Exa API key from [exa.ai](https://exa.ai) |

---

## Project structure

```
exa_gov_contractors/
├── main.py              # FastAPI app — routes + Exa API calls
├── templates/
│   ├── base.html        # Shared nav, footer, Tailwind config
│   ├── govtrack.html    # GovTrack UI + JS
│   └── brief.html       # Value prop one-pager
├── requirements.txt
├── .env.example
└── README.md
```

---

## Business case

### ExaGov — Federal Procurement Intelligence for Growth-Stage Contractors

#### 1. The Problem

- $700B in federal contracts awarded annually, but discovery is broken.
- BD managers spend 2+ hours daily across SAM.gov, Google, and trade press manually.
- GovWin costs $15K/year, out of reach for most mid-market firms.

#### 2. Why Exa Wins

- Semantic search finds intent-matched RFPs that keyword tools miss.
- Multi-source ingestion combines SAM.gov, USASpending, and agency news in one query.
- Real-time indexing surfaces opportunities 24-48 hours before aggregators.

#### 3. Market Opportunity

| Metric | Value |
|---|---|
| Total federal procurement | **$737B** |
| Active mid-market contractors | **~130,000** |
| Addressable at $200/month | **10,000-30,000 firms** |
| ARR potential | **$24M-$72M** |

#### 4. Pilot Design (3 Weeks)

| Week | Milestone |
|---|---|
| **Week 1** | Run current searches and compare output vs SAM.gov. |
| **Week 2** | Surface 3 RFPs missed by keyword search. |
| **Week 3** | Pull incumbent intel on top pipeline opportunities. |

#### 5. Sales Barriers

| Barrier | Response |
|---|---|
| Risk aversion: "We already use GovWin." | Run a side-by-side pilot using their live pipeline queries and show measurable lift. |
| Security onboarding friction | Position ExaGov as read-only retrieval with cited sources and no PII ingestion. |
| "SAM.gov is free" | Reframe to labor ROI: 2 hours/day manual search is materially more expensive than $200/month. |

### Supplemental Research Appendix

#### 1. Competitive Landscape Synthesis

| Solution | Typical Price | Coverage | Retrieval Style | Mid-Market Fit |
|---|---|---|---|---|
| **GovWin IQ** | $12K-$18K/yr | Deep contract + relationship intel | Keyword / filter-heavy | Low (cost + complexity) |
| **Bloomberg Government** | ~$15K/yr | Broad policy + procurement signals | Keyword + newsroom workflow | Low-Medium |
| **GovTribe / Govly** | $2K-$6K/yr | Opportunity monitoring | Keyword-centered discovery | Medium |
| **SAM.gov + USASpending** | Free | Authoritative point sources | Manual search / lookup | High (time-cost heavy) |
| **ExaGov** | ~$200/mo | SAM + spending + news unified | Semantic retrieval + recency filters | **High** |

#### 2. Persona Synthesis

- Primary: Capture Manager / BD Director
  Firm profile: $5M-$50M revenue, 20-250 employees.
  Core pain: fragmented discovery stack and missed RFP windows.
  Success metric: more qualified opportunities per week.
- Secondary: SBIR / 8(a) Emerging Teams
  Firm profile: early-stage entrants with lean BD capacity.
  Core pain: cannot justify enterprise intelligence tooling.
  Success metric: first repeatable pipeline with incumbent context.

#### 3. Usage Cadence Breakdown

| Workflow | Share |
|---|---|
| Daily: New RFP monitoring | 40% |
| Weekly: Pipeline triage + qualification | 30% |
| Monthly: Agency signal tracking | 20% |
| Pre-proposal: Incumbent deep-dive | 10% |

#### 4. Why This Market Is Under-Served

| Market Friction | Observed Impact | ExaGov Positioning |
|---|---|---|
| Fragmented source landscape | Analysts switch tools all day; high context loss | Unified retrieval surface with one query workflow |
| Keyword-first incumbent tools | Intent mismatch causes missed opportunities | Semantic search captures meaning over phrasing |
| Pricing mismatch for mid-market | High-end products price out core users | $200/month wedge with measurable labor ROI |
