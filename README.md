Email Sentiment Analysis Dashboard
This project is a Flask-based web application that fetches emails from a Gmail account, performs sentiment analysis on them using a local Ollama model, and displays the results on a dashboard.

Features

Gmail Integration: Authenticates with the Gmail API to fetch unread emails from the inbox.



Sentiment Analysis: Utilizes a local Ollama server to classify email sentiment as "positive," "negative," or "neutral".


Team Assignment: Automatically assigns emails to a team ("Feedback," "Support," or "Operations") based on the analyzed sentiment.


Database Storage: Stores parsed emails, their sentiment, and scores in a local SQLite database.


Web Dashboard: A user-friendly web interface built with Flask and Tailwind CSS to visualize email sentiment data.


Interactive Graph: Displays email sentiment distribution using a bar chart on a dedicated graph page.

Prerequisites
Python 3.x

A Google Account with API credentials set up for Gmail API access.

Ollama installed and running locally with the 

yi:9b model.

Installation and Setup
Clone the repository:

Bash

git clone <repository-url>
cd <repository-folder>
Install dependencies:

Bash

pip install Flask google-api-python-client google-auth-oauthlib
Set up Google API Credentials:

Follow the Google documentation to enable the Gmail API and download your credentials.json file.

Place the credentials.json file in the project's root directory. The 

gmail_auth.py script will use this to authenticate.

Set up the Database:

Run the 

init_db.py script to create the emails.db file and the emails table.

Bash

python init_db.py
Set up Ollama:

Ensure Ollama is running on 

http://localhost:11434 with the yi:9b model available for chat. The 

ollama_utils.py script is configured to use this endpoint.

Usage
Run the Flask application:

Bash

python app.py
Access the Dashboard:

Open your web browser and navigate to http://127.0.0.1:5000/.

Click "Refresh Emails" on the dashboard to fetch new emails from your inbox and perform sentiment analysis.

Navigate between the dashboard and the graph view to see different representations of the data.

File Structure

app.py: Main Flask application file.


fetch_emails.py: Script for fetching, parsing, and storing emails.


gmail_auth.py: Handles Google API authentication.


email_utils.py: Contains functions to parse email data from the Gmail API.


ollama_utils.py: Manages the sentiment analysis using Ollama.


init_db.py: Database initialization script.


emails.db: The SQLite database file.


base.html: The base HTML template for the web interface.


dashboard.html: The HTML template for the sentiment dashboard.


graph.html: The HTML template for the sentiment graph view.
