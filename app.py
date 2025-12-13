import os
import json
import time
import re
import requests
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, redirect, url_for, request, session
from datetime import datetime
from pytz import timezone, utc
import logging

from emails_db import get_all_emails, get_stats, get_sentiment_counts_for_graph
from process_emails import process_unread_emails
from email_utils import clean_email_body

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)

load_dotenv("secretkeys.env")
app.secret_key = os.getenv('FLASK_SECRET_KEY') 

PREDEFINED_USER_EMAIL = os.getenv('USERNAME')
PREDEFINED_PASSWORD = os.getenv('PASSWORD')

LOCAL_TZ = timezone('Asia/Kolkata')  # IST

def format_datetime(dt: datetime) -> str:
    """Formats a UTC datetime object to a local timezone string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=utc)
    
    local_dt = dt.astimezone(LOCAL_TZ)
    return local_dt.strftime('%b %d, %Y %I:%M %p %Z')

@app.context_processor
def utility_processor():
    """Makes functions available in Jinja templates."""
    return dict(format_datetime=format_datetime)

def login_required(f):
    """Decorator to ensure user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@app.route('/dashboard')
@login_required
def index():
    """Main dashboard showing emails and stats."""
    emails = get_all_emails(limit=10) 
    stats = get_stats()
    sentiment_counts = get_sentiment_counts_for_graph()
    
    for email in emails:
        ts = email.get('timestamp')
        if isinstance(ts, datetime):
            email['timestamp'] = format_datetime(ts)
            
        sentiment = email.get('ai_sentiment')
        if not sentiment or sentiment.title() in ['Llm_Failed', 'Unclassified']:
            email['ai_sentiment'] = 'Neutral'
        else:
            email['ai_sentiment'] = sentiment.title()

    return render_template('dashboard.html', emails=emails, stats=stats, sentiment_counts=sentiment_counts)

@app.route('/sentiment-graph')
@login_required
def sentiment_graph():
    """Renders the graph view."""
    sentiment_counts = get_sentiment_counts_for_graph()
    return render_template('graph.html', sentiment_counts=sentiment_counts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if request.method == 'POST':
        email_input = request.form.get('email')
        password_input = request.form.get('password')

        if email_input == PREDEFINED_USER_EMAIL and password_input == PREDEFINED_PASSWORD:
            session['logged_in'] = True
            log.info(f"User {email_input} logged in successfully.")
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        else:
            log.warning(f"Failed login attempt for user: {email_input}")
            return render_template('login.html', error='Invalid credentials.'), 401
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Handles user logout."""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/api/refresh', methods=['POST'])
@login_required
def api_refresh():
    """
    API endpoint to trigger email fetching and return updated data (user initiated).
    """
    error_message = None
    new_count = 0
    try:
        new_count = process_unread_emails(limit=5)
    except Exception as e:
        log.error(f"Error processing emails via API refresh: {e}", exc_info=True)
        error_message = f"An error occurred during email fetching: {e}"

    try:
        emails = get_all_emails(limit=10)
        stats = get_stats()
    except Exception as e:
        log.error(f"Error fetching data after processing: {e}", exc_info=True)
        return jsonify({"error": "Database read failed", "new_count": new_count}), 500

    for email in emails:
        email['body'] = clean_email_body(email.get('body', ''))
        
        ts = email.get('timestamp')
        if isinstance(ts, datetime):
            email['timestamp'] = format_datetime(ts)
            
        sentiment = email.get('ai_sentiment')
        if not sentiment or sentiment.title() in ['Llm_Failed', 'Unclassified']:
            email['ai_sentiment'] = 'Neutral' 
        else:
            email['ai_sentiment'] = sentiment.title()
            
    response = {"emails": emails, "stats": stats, "new_count": new_count}
    if error_message:
        response["error"] = error_message

    return jsonify(response)


@app.route('/api/scheduled_fetch', methods=['GET'])
def scheduled_fetch():
    """
    New API endpoint triggered by Vercel Cron Job to run the background task.
    This replaces the local fetch_loop.py file.
    """
    log.info("Triggered by Vercel Cron Job.")
    try:
        count = process_unread_emails(limit=5) 
        log.info(f"Scheduled job processed {count} new unread emails.")
        return jsonify({"status": "success", "processed_count": count}), 200
    except Exception as e:
        log.error(f"Error during scheduled email fetch: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    try:
        from emails_db import recreate_table
        recreate_table()
        log.info("Database table ensured/recreated for fresh start.")
    except Exception as e:
        log.error(f"Could not initialize database: {e}", exc_info=True)

    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5001), debug=True)
