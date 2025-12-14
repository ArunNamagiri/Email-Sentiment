📧 Email Sentiment Analysis

Tired of shifting through hundreds of emails just to find the urgent ones?
This Flask web application acts as your personal inbox analyst — automatically prioritizing your messages based on sentiment (**Positive**, **Negative**, or Neutral) using Google’s Gemini AI.

Get a real-time overview of your inbox’s “mood,” ensuring you never miss a critical message or an important compliment.

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

🚀 End-to-End Analysis Workflow: Step-by-Step

This project executes a sophisticated, automated pipeline every time the data refresh is triggered.  
Below is the chronological flow of how an unread email is processed, analyzed, and displayed.

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

🧩 Phase 1: Data Ingestion and Isolation

- Connection & Authentication:
  Secure connection to Gmail IMAP server (`imap.gmail.com`) using a Gmail App Password.

- Unread Isolation:
  Executes `UID SEARCH UNSEEN` to fetch only *unread* emails — ensuring efficiency and idempotency.

- Data Retrieval & Decoding:
  Fetches sender, subject, and body, decoding UTF-8 and other encodings to correctly handle all characters.

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

 🤖 Phase 2: AI Transformation and Structure

LLM Request Construction: 
  Builds a structured request to the **Gemini API, including:
  - Email Body: Raw text to analyze.  
  - System Instruction: Prompted as a “World-Class Sentiment Analyst.”
  - Low Temperature (0.1):Ensures deterministic, reliable results.  
  - API Key Injection:Injected securely as a query parameter.  
  - Strict JSON Schema: Guarantees predictable structured output with:
    ```json
    {
      "sentiment": "Positive | Negative | Neutral",
      "summary": "Brief overview of email content",
      "suggested_reply": "AI-generated suggested response"
    }
    ```

Reliability & Retry:
  Implements exponential backoff for transient API or network issues to ensure resilience.

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

 💾 Phase 3: Persistence and Presentation

- Data Integrity Check:
  Verifies each email’s UID before saving to avoid duplicates.

- Database Persistence:
  Stores UID, sender, sentiment, and summary in a **Neon PostgreSQL** database via `psycopg2`.

- Dashboard Retrieval:
  Queries the database and computes aggregate stats (Positive / Negative / Neutral counts).

- Rendering:
  Displays results through a **Flask + Jinja2** dashboard with sentiment cards and tabular history.

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

⚙️ Installation and Setup

🛠️ Prerequisites
- Python 3.10 +
- Gmail Account with [App Password](https://support.google.com/mail/answer/185833)
- PostgreSQL Database (recommended: [Neon](https://neon.tech))
- Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/email-sentiment-analysis.git
cd email-sentiment-analysis

2️⃣ Environment Setup
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt

3️⃣ Configure Secrets

Create a file named secretkeys.env in the project root:

# Gmail Credentials
GMAIL_USER="your.email@gmail.com"
GMAIL_PASS="your_gmail_app_password"

# Database Configuration
DATABASE_URL="postgres://user:password@host:port/dbname"

# LLM API Configuration (Gemini)
LLM_API_URL="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
LLM_API_KEY="AIza......your-gemini-key"
LLM_MODEL="gemini-2.5-flash"

4️⃣ Run Locally
# Optional: Clear database
python reset_db.py

# Start Flask app
python app.py
Access the dashboard at 👉 http://127.0.0.1:5000/dashboard

☁️ Deploying to Vercel

Add vercel.json to the project root (configures Python runtime).

Add Environment Variables in Vercel → Project Settings → Environment Variables.

Push to GitHub — Vercel will auto-deploy your app.

🧠 Tech Stack
| Component         | Technology        |
| ----------------- | ----------------- |
| Backend           | Flask             |
| Frontend          | Jinja2, HTML, CSS |
| Database          | Neon PostgreSQL   |
| AI Model          | Gemini 2.5 Flash  |
| Deployment        | Vercel            |
| Email Integration | Gmail IMAP        |
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

💡 Inspiration


This project was built to blend AI-powered sentiment analysis with real-world email management, turning your inbox into a smart, emotional dashboard.
