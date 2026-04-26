# GovTrack & LegalEdge — Exa Market Intelligence Demo

Two vertical applets demonstrating Exa's semantic search capabilities in markets outside tech and finance: **government contracting** and **legal research**.

## Live demos

| Route | Tool | Target user |
|---|---|---|
| `/` | Landing page | — |
| `/govtrack` | RFP Intelligence | Mid-market gov contractors |
| `/legaledge` | Legal Research | Small law firms / in-house |

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

### LegalEdge (`/legaledge`)
1. User types a practice area + jurisdiction (e.g. *"HIPAA compliance healthcare"*).
2. Backend searches CourtListener, law.cornell.edu, FederalRegister.gov, and legal news.
3. Results tagged as **Case Law / Regulation / Statute / Legal News**.

Both tools fall back to a broader (no-domain) Exa search if the targeted domains return zero results.

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
│   ├── index.html       # Landing page
│   ├── govtrack.html    # GovTrack UI + JS
│   └── legaledge.html   # LegalEdge UI + JS
├── requirements.txt
├── .env.example
└── README.md
```

---

## Business case (one paragraph)

The US government spends **$700B+/year** on contracts. Tens of thousands of small businesses compete for these contracts using Google, PDF filings, and expensive legacy platforms like GovWin IQ ($12–18K/year). Exa's semantic search — which retrieves by *meaning* rather than keywords — can surface relevant RFPs, identify incumbents, and track agency priorities in real time at a fraction of the cost. The same logic applies to legal research: Westlaw and LexisNexis cost $5K–$20K/year, pricing out solo practitioners and small firms. Both markets are **information-dense, time-critical, and historically ignored by AI vendors** — making them ideal expansion targets for Exa.
