import os
import logging
import requests
import json
import re

log = logging.getLogger(__name__)

LLM_API_URL = os.getenv("LLM_API_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma:2b")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20")) 

def llm_analyze_email(body: str, subject: str) -> dict:
    if not LLM_API_URL:
        return {
            "sentiment": "Neutral",
            "summary": "LLM not configured.",
            "suggested_reply": "Manual review required."
        }

    prompt = f"""
Return ONLY valid JSON.

{{
  "sentiment": "Positive | Negative | Neutral",
  "summary": "Short summary",
  "suggested_reply": "Professional reply"
}}

Subject: {subject}
Body:
{body}
"""

    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    }

    text = ""   

    try:
        response = requests.post(
            LLM_API_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        text = response.json().get("response", "").strip()

        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found")

        data = json.loads(match.group(1))

        sentiment_raw = str(data.get("sentiment", "Neutral")).lower()
        if "positive" in sentiment_raw:
            sentiment = "Positive"
        elif "negative" in sentiment_raw:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        return {
            "sentiment": sentiment,
            "summary": str(data.get("summary", "")),
            "suggested_reply": str(data.get("suggested_reply", ""))
        }

    except requests.exceptions.Timeout:
        log.error("Ollama timeout")

    except requests.exceptions.RequestException as e:
        log.error(f"Ollama error: {e}")

    except (ValueError, json.JSONDecodeError) as e:
        log.error(f"JSON parse error: {e}")

    sentiment_match = re.search(r'"sentiment"\s*:\s*"([^"]+)"', text, re.I)
    summary_match = re.search(r'"summary"\s*:\s*"([^"]+)"', text, re.I)
    reply_match = re.search(r'"suggested_reply"\s*:\s*"([^"]+)"', text, re.I)

    sentiment = sentiment_match.group(1) if sentiment_match else "Neutral"
    summary = summary_match.group(1) if summary_match else "LLM failed"
    reply = reply_match.group(1) if reply_match else "Please review manually"

    s = sentiment.lower()
    if "positive" in s:
        sentiment = "Positive"
    elif "negative" in s:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    return {
        "sentiment": sentiment,
        "summary": summary,
        "suggested_reply": reply
    }
