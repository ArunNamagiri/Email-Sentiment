import os
import threading
import logging
from functools import wraps
from flask import Flask, render_template, jsonify, redirect, url_for, request, session
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta 

# Imports are now safe and linear, as email_sender no longer imports app.
from process_emails import has_unread_emails, process_unread_emails
from emails_db import create_emails_table
from emails_db import (
    get_all_emails,
    get_stats,
    get_sentiment_counts_for_graph,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
create_emails_table()
load_dotenv("secretkeys.env")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")


# --- Custom Jinja Filter for IST Conversion (Defined and Registered here) ---
def utc_to_ist(utc_dt) -> str:
    """Converts a UTC datetime object or string to IST (UTC + 5:30) and formats it."""
    if isinstance(utc_dt, str):
        try:
            # Parse from string, handling potential microseconds
            utc_dt = datetime.strptime(utc_dt.split('.')[0], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Fallback for unexpected formats
            utc_dt = datetime.now(timezone.utc)

    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        
    # IST is UTC + 5 hours 30 minutes
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    ist_dt = utc_dt.astimezone(ist_timezone)
    
    # Format: 14-Dec-2025 10:30 PM
    return ist_dt.strftime("%d-%b-%Y %I:%M %p")

# Register the filter with the Flask app instance
app.jinja_env.filters['to_ist'] = utc_to_ist


# ---------- AUTH ----------
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrap


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["email"] == USERNAME and request.form["password"] == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template(
        "dashboard.html",
        emails=get_all_emails(),
        stats=get_stats(),
        sentiment_counts=get_sentiment_counts_for_graph()
    )


@app.route("/graph")
@login_required
def sentiment_graph():
    return render_template(
        "graph.html",
        sentiment_counts=get_sentiment_counts_for_graph()
    )


@app.route("/api/refresh", methods=["POST"])
@login_required
def refresh():
    count = process_unread_emails(limit=3)

    return jsonify({
        "status": "done",
        "processed": count
    }), 200


# ---------- API DATA ENDPOINT ----------
# app.py (inside api_stats function)

@app.route("/api/stats")
@login_required
def api_stats():
    stats = get_stats()
    emails = get_all_emails()   

    emails_list = []
    for email in emails:
        emails_list.append({
            "id": email["id"],
            "sender": email["sender"],
            "subject": email["subject"],
            "body": email["body"],
            "ai_sentiment": email["ai_sentiment"],
            "summary": email["summary"],
            "suggested_reply": email["suggested_reply"],
            "forwarded_to_team": email.get("forwarded_to_team", "N/A"),
            "timestamp": utc_to_ist(email["timestamp"])
        })

    return jsonify({
        "emails": emails_list,
        "stats": stats
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001, host="0.0.0.0")