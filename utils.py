import httpx
from bs4 import BeautifulSoup
import time

def check_website(url: str):
    result = {
        "url": url,
        "timestamp": time.time(),
        "status_code": None,
        "load_time": None,
        "title": None,
        "meta_description": None,
        "alerts": [],
    }

    try:
        start = time.time()
        response = httpx.get(url, timeout=10)
        result["status_code"] = response.status_code
        result["load_time"] = round(time.time() - start, 2)

        soup = BeautifulSoup(response.text, "html.parser")
        result["title"] = soup.title.string if soup.title else None

        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            result["meta_description"] = meta["content"]
        else:
            result["alerts"].append("Missing meta description")

        if response.status_code != 200:
            result["alerts"].append(f"Non-200 status: {response.status_code}")

    except Exception as e:
        result["alerts"].append(f"Error: {str(e)}")

    return result
