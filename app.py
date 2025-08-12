from flask import Flask, render_template, redirect, url_for
from fetch_emails import fetch_and_store_emails
from db_utils import get_all_emails, get_sentiment_summary
import threading
from fetch_emails import fetch_and_store_emails

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    emails = get_all_emails()
    return render_template('dashboard.html', emails=emails)

@app.route('/graph')
def graph():
    sentiment_data = get_sentiment_summary()
    return render_template('graph.html', sentiment_data=sentiment_data)

# @app.route('/refresh_emails')
# def refresh_emails():
#     fetch_and_store_emails()
#     return redirect(url_for('dashboard'))

@app.route('/refresh_emails')
def refresh_emails():
    threading.Thread(target=fetch_and_store_emails).start()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(port=50001, debug=False)

