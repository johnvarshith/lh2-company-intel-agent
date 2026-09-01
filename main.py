import os, json, logging, asyncio
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from supabase import create_client
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scraper import scrape_company
from llm_judge import judge_company

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = FastAPI(title="LH2 Company Intelligence Agent")

# --- CONFIG ---
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
GOOGLE_CREDS_JSON = os.environ["GOOGLE_CREDS_JSON"]
SHEET_ID = os.environ["SHEET_ID"]
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "default-secret")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- SHEETS AUTH ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GOOGLE_CREDS_JSON), scope)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).sheet1

def get_pending_rows():
    records = sheet.get_all_records()
    return [
        {"row_num": idx + 2, "company": r.get("Company"), "website": r.get("Website")}
        for idx, r in enumerate(records)
        if str(r.get("Status", "")).strip() == ""
    ]

async def process_pipeline():
    logging.info("🚀 Pipeline run started")
    pending = get_pending_rows()
    if not pending:
        logging.info("✅ No new rows. Pipeline idle.")
        return

    for item in pending:
        company, website, row_num = item["company"], item["website"], item["row_num"]
        logging.info(f"Processing: {company}")

        # ENRICH
        signal_browser = await scrape_company(website)
        signal_http = {"domain_length": len(website), "has_www": "www" in website}
        signals = {"browser": signal_browser, "http": signal_http}

        # PERSIST
        supabase.table("company_intel").insert({
            "company_name": company, "website": website,
            "signals": signals, "sheet_row": row_num, "processed": False
        }).execute()

        # JUDGE
        verdict = judge_company(company, signals)

        # UPDATE DB
        supabase.table("company_intel").update({
            "verdict": verdict, "processed": True
        }).eq("sheet_row", row_num).execute()

        # SYNC BACK TO SHEET
        sheet.update_cell(row_num, 3, "Processed")
        sheet.update_cell(row_num, 4, f"{verdict['fit_call']} ({verdict['confidence']}%)")
        sheet.update_cell(row_num, 5, verdict["reasoning"])

        logging.info(f"✅ Completed: {company} → {verdict['fit_call']}")

# --- SCHEDULER (Req 6: fires on schedule without restart) ---
@app.on_event("startup")
async def startup():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(process_pipeline, 'interval', minutes=5, id="auto_poll")
    scheduler.start()
    logging.info("⏰ Scheduler started: polling every 5 min")

# --- ENDPOINTS (Req 6: triggerable + queryable) ---
@app.post("/trigger")
async def trigger(bg: BackgroundTasks):
    bg.add_task(process_pipeline)
    return {"status": "Pipeline triggered in background"}

@app.get("/verdicts")
async def get_verdicts():
    return supabase.table("company_intel").select("*").order("id", desc=True).limit(50).execute().data

class WebhookPayload(BaseModel):
    secret: str

@app.post("/github-trigger")
async def github_trigger(payload: WebhookPayload, bg: BackgroundTasks):
    if payload.secret != WEBHOOK_SECRET:
        return {"status": "unauthorized"}
    bg.add_task(process_pipeline)
    return {"status": "success"}

@app.get("/")
async def health():
    return {"agent": "lh2-company-intel-agent", "status": "running"}
