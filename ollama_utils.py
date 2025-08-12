import requests
import json

def analyze_sentiment(text):
    url = "http://localhost:11434/api/chat"
    model = "yi:9b"

    prompt = f"""
    You are an expert sentiment analysis bot. Your task is to analyze the sentiment of a given email text and classify it as either "positive", "negative", or "neutral".
    Provide your response as a JSON object with two keys: "sentiment" and "score".

    Email Text:
    '{text}'

    Example: {{"sentiment": "positive", "score": 0.75}}
    """

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = json.loads(response.json()["message"]["content"])
        return result.get("sentiment", "neutral"), result.get("score", 0.0)
    except Exception as e:
        print(f"[Ollama error] {e}")
        return "neutral", 0.0
