from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import requests
import traceback
from dotenv import load_dotenv
from alexa_routes import router as alexa_router

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# CORS middleware for frontend/backend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Slack Integration
def send_slack_alert(message: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if webhook_url:
        try:
            response = requests.post(webhook_url, json={"text": message})
            if response.status_code != 200:
                print(f"Slack error: {response.text}")
        except Exception as e:
            print(f"Slack alert failed: {e}")
            traceback.print_exc()

# Zapier Integration
def trigger_zapier_webhook(event: str, data: dict):
    zapier_url = os.getenv("ZAPIER_WEBHOOK_URL")
    if zapier_url:
        try:
            response = requests.post(zapier_url, json={"event": event, "data": data})
            if response.status_code != 200:
                print(f"Zapier error: {response.text}")
        except Exception as e:
            print(f"Zapier trigger failed: {e}")
            traceback.print_exc()

# Request models
class ChatRequest(BaseModel):
    message: str

class MonitorRequest(BaseModel):
    url: str

class SummaryRequest(BaseModel):
    uptime: str
    response_time: str
    seo: str
    ssl: str

# GPT Chatbot Route
@app.post("/chat")
async def chat_endpoint(data: ChatRequest):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant for website monitoring and performance."},
                {"role": "user", "content": data.message}
            ]
        )
        reply = response['choices'][0]['message']['content']
        return {"response": reply}
    except Exception as e:
        print("OpenAI Chat Error:", e)
        traceback.print_exc()
        return {"response": "⚠️ Chat failed. Please try again."}

# Start Monitoring Route
@app.post("/start-monitoring")
async def start_monitoring(data: MonitorRequest):
    print(f"Start monitoring: {data.url}")
    send_slack_alert(f"Monitoring started for: {data.url}")
    trigger_zapier_webhook("start_monitoring", {"url": data.url})
    return {"status": "started", "url": data.url}

# Generate AI Summary
@app.post("/summary")
async def generate_summary(data: SummaryRequest):
    prompt = (
        f"Summarize this website's performance:\n"
        f"- Uptime: {data.uptime}\n"
        f"- Response Time: {data.response_time}\n"
        f"- SEO: {data.seo}\n"
        f"- SSL: {data.ssl}\n"
        f"Return a short, helpful summary in plain language."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a website monitoring assistant that summarizes site status for users."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        summary = response['choices'][0]['message']['content']
        return {"summary": summary}
    except Exception as e:
        return {"summary": f"⚠️ API error: {str(e)}"}

# Include Alexa-compatible endpoints
app.include_router(alexa_router)

# Root check
@app.get("/")
def root():
    return {"message": "SitePulseAI full backend is running."}


       
