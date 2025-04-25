from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread
import time
import os
from dotenv import load_dotenv
import openai
from monitor import check_website

# === Load environment variables ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# === Config ===
MONITORED_URL = "https://example.com"  # Replace with your actual URL
CHECK_INTERVAL = 60  # seconds

app = FastAPI()

# === Enable CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your frontend URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Store latest results ===
latest_results = {}

# === Background monitoring thread ===
def background_monitor():
    while True:
        result = check_website(MONITORED_URL)
        latest_results[MONITORED_URL] = result
        time.sleep(CHECK_INTERVAL)

@app.on_event("startup")
def start_background_thread():
    thread = Thread(target=background_monitor, daemon=True)
    thread.start()

# === Routes ===
@app.get("/status")
def get_status():
    return latest_results.get(MONITORED_URL, {})

@app.get("/alerts")
def get_alerts():
    return latest_results.get(MONITORED_URL, {}).get("alerts", [])

@app.get("/insights")
def get_insights():
    site_data = latest_results.get(MONITORED_URL, {})

    prompt = f"""
    You are an AI assistant reviewing a website. Here's the data:
    - Status Code: {site_data.get('status_code')}
    - Load Time: {site_data.get('load_time')}
    - Title: {site_data.get('title')}
    - Meta Description: {site_data.get('meta_description')}
    - Alerts: {site_data.get('alerts')}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        insight = response.choices[0].message.content
    except Exception as e:
        insight = f"Error generating insight: {str(e)}"

    return {"url": MONITORED_URL, "insight": insight}
from fastapi import Request
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": request.message}]
        )
        reply = response.choices[0].message.content.strip()
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}



