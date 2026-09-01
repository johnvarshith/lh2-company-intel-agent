# 🤖 LH2 Company Intelligence Agent

An end-to-end, autonomous B2B lead qualification agent. It ingests a list of companies from a Google Sheet, autonomously browses the web to gather intelligence, reasons over the evidence using an LLM, and writes structured verdicts back to the sheet—all without human intervention.

**🔗 Live App & API Docs:** [Insert your Render URL here]/docs  
**📂 GitHub Repository:** [Insert your GitHub Repo Link here]  
**🎥 Demo Video Walkthrough:** [Insert your Loom/YouTube Video Link here]  

---

## 🏗️ Architecture Flow

```text
[Google Sheet] ──(1. Polling)──> [FastAPI Orchestrator]
                                       │
                       ┌───────────────┴───────────────┐
                       ▼                               ▼
               [Playwright Browser]             [HTTP / API Signals]
               (JS Rendering, DOM)              (Domain metadata, etc.)
                       │                               │
                       └───────────────┬───────────────┘
                                       ▼
                              [Supabase PostgreSQL]
                              (Persistent Storage)
                                       │
                                       ▼
                              [Groq LLM (Judge)]
                              (Structured JSON)
                                       │
                                       ▼
                              [Google Sheet Sync]
                              (Verdict & Reasoning)
```

---

## 🛠️ Tech Stack & Design Decisions

The assignment specified "free-tier tools only - your choice which ones. That's part of what we're evaluating." Here is the rationale behind the architectural choices:

| Component | Tool Chosen | Why I chose it |
| :--- | :--- | :--- |
| **Framework** | **FastAPI** | Native `asyncio` support is critical for running background polling tasks and non-blocking browser automation concurrently without spawning heavy thread pools. |
| **Browser Automation** | **Playwright** | Standard HTTP requests (`requests`/`BeautifulSoup`) can fail on modern JS-heavy SPAs. Playwright provides real headless Chromium to capture rendered DOM content. |
| **Database** | **Supabase** | The prompt required a real database rather than memory or direct Sheet writes. Supabase provides managed PostgreSQL with `JSONB` support for storing unstructured scraping signals. |
| **LLM Judge** | **Groq API** | Groq provides fast LLM inference. Structured JSON output keeps the verdict predictable and prevents malformed model responses from breaking the pipeline. |
| **Hosting** | **Render (Docker)** | Containerized deployment provides environment parity. The deployment is optimized for Render's free-tier memory constraints by using Chromium launch flags such as `--disable-dev-shm-usage`. |
| **Scheduling** | **APScheduler + GitHub Actions** | Dual-trigger architecture. APScheduler polls the sheet periodically, while GitHub Actions provides an external cron trigger for the deployed application. |

---

## ✅ Fulfillment of Assignment Requirements

1. **Source:** Uses `gspread` with a Google Cloud Service Account to poll the Google Sheet every 5 minutes via `APScheduler`. New rows are picked up dynamically without restarting the application.
2. **Enrich:** Extracts company signals using **Playwright**, including rendered page content and metadata, along with HTTP-level signals.
3. **Persist:** Stores raw scraped text, HTTP signals, processing information, and LLM verdicts in a **Supabase PostgreSQL** table named `company_intel`.
4. **Judge:** Uses the Groq LLM to evaluate collected signals against a structured system prompt and return:
   - `fit_call`
   - `confidence`
   - `reasoning`
   - `follow_up_question`
5. **Sync Back:** Maps the JSON verdict to the appropriate row and columns in the Google Sheet using authenticated Service Account credentials.
6. **Run Itself:**
   - **Scheduled:** Internal APScheduler + external GitHub Actions Cron.
   - **Triggerable:** `POST /trigger` endpoint.
   - **Queryable:** `GET /verdicts` endpoint reads verdicts from Supabase.
7. **Ship:** Fully containerized with a `Dockerfile` and deployed to a reachable Render URL.
8. **Wire It to GitHub:**
   - `ci.yml` runs `flake8` linting on every push.
   - `schedule.yml` triggers the live application using a scheduled cron or manual `workflow_dispatch`.

---

## 🧪 How to Test the Live App

1. Open the **[Live API Docs](Insert your Render URL here/docs)**.
2. Find the `POST /trigger` endpoint.
3. Click **Try it out**.
4. Click **Execute**.
5. Open the **[Target Google Sheet](Insert your Google Sheet Link here)**.
6. Watch the `Status`, `Fit`, and `Reasoning` columns update.
7. Optionally, use the `GET /verdicts` endpoint to query stored results directly from the database.

---

## 💻 Local Development

### 1. Clone the repository

```bash
git clone <repo-url>
cd <repo-folder>
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure environment variables

Create a `.env` file containing:

```env
SUPABASE_URL=
SUPABASE_KEY=
GROQ_API_KEY=
SHEET_ID=
GOOGLE_CREDS_JSON=
WEBHOOK_SECRET=
```

### 4. Run the application

```bash
uvicorn main:app --reload --port 8000
```

The API documentation will then be available at:

```text
http://localhost:8000/docs
```

---

## 📂 Repository Structure

```text
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI / linting workflow
│       └── schedule.yml        # Scheduled webhook trigger
│
├── Dockerfile                  # Container configuration
├── requirements.txt            # Python dependencies
├── main.py                     # FastAPI orchestrator, endpoints & scheduler
├── scraper.py                  # Playwright browser automation
├── llm_judge.py                # Groq LLM integration & prompt logic
└── README.md                   # Project documentation
```

---

## 🔄 End-to-End Workflow

```text
1. Google Sheet
       ↓
2. APScheduler detects new company
       ↓
3. Playwright visits company website
       ↓
4. HTTP + rendered DOM signals collected
       ↓
5. Raw intelligence persisted to Supabase
       ↓
6. Groq LLM evaluates evidence
       ↓
7. Structured JSON verdict generated
       ↓
8. Verdict stored in Supabase
       ↓
9. Google Sheet updated
```

---

## 🔐 Security & Configuration

Sensitive credentials should never be committed to the repository.

Use environment variables or your hosting provider's secret-management system for:

- Supabase credentials
- Groq API key
- Google Service Account credentials
- Google Sheet ID
- Webhook secret

Make sure `.env` and other credential files are included in `.gitignore`.

---

## 🎯 Key Engineering Highlights

- **Autonomous workflow:** The system can continuously discover and process new companies without manual execution.
- **Browser-based enrichment:** Playwright handles JavaScript-rendered websites that basic HTTP scraping may not capture correctly.
- **Persistent audit trail:** Raw evidence and model decisions are stored instead of keeping results only in memory.
- **Structured LLM output:** The judge produces machine-readable JSON for reliable downstream processing.
- **Multiple execution paths:** Supports scheduled polling, external cron triggering, and manual API triggering.
- **Containerized deployment:** Docker keeps the runtime environment consistent between development and production.
- **API-first design:** FastAPI provides interactive Swagger documentation and simple endpoints for triggering and querying the pipeline.

---

## 🚀 Future Improvements

Potential extensions include:

- Parallel processing of multiple companies.
- Retry and exponential-backoff handling for failed websites.
- More advanced company-data enrichment sources.
- Improved evidence scoring and confidence calibration.
- Deduplication and change detection for previously processed companies.
- Authentication and rate limiting for public API endpoints.
- Observability with structured logs and processing metrics.

---

## 👨‍💻 Author

**varshith


Built for the **LH2 AI Labs Automation Intern Assignment**.

*Built with ☕ and 🚀.*
