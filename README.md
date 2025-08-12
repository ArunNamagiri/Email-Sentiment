📧 Email Sentiment Analyzer (Flask + Ollama + Gmail API)
This project automatically analyzes the sentiment of incoming Gmail emails using local LLMs via Ollama and organizes them into Positive, Negative, or Neutral categories.
It stores results in a MySQL database, displays them on an interactive Flask dashboard, and forwards emails to different Gmail addresses based on sentiment.
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
✨ Features
📬 Fetch Unread Emails directly from Gmail API

🧠 Sentiment Analysis using local Ollama LLMs (Gemma 2B & Yi 9B)

📊 Interactive Dashboard with filters by sentiment, sender, and date

🗂 MySQL Database to store email history & sentiment results

📤 Automatic Email Forwarding to team inboxes based on sentiment

🔄 Refresh Button to update dashboard with latest unread emails
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
🧪 Model Comparison

| Model   | Pros                                  | Cons                               |
| ------- | ------------------------------------- | ---------------------------------- |
| Yi 9B   | Identifies more sentiment-driving keywords | Occasionally over-labels sentiment |
| Gemma 2B| More consistent and conservative           | May miss subtle emotional cues     |

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
⚙️ Project Architecture

📦 Email_Sentiment_dashboard
│
├── 📁 templates/  
│   └── 📝 dashboard.html — HTML for Flask dashboard  
│
├── 📁 static/ — CSS, JS, images (optional)  
├── 📁 venv/ — Python virtual environment  
│
├── 🔑 .env — Environment variables (API keys, DB creds)  
├── 🚀 app.py — Flask app entry point  
├── 📬 fetch_loop.py — Gmail fetcher & sentiment processor  
├── 🤖 process_email.py — Model sentiment classification logic  
├── 🗄️ database.sql — MySQL table schema  
├── 📦 requirements.txt — Python dependencies  
└── 📘 README.md — Project documentation


-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
🚀 Setup & Usage

1️⃣ Clone the repository

git clone https://github.com/yourusername/email_sentiment_dashboard.git
cd email_sentiment_dashboard

2️⃣ Create and activate virtual environment

python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

3️⃣ Install dependencies

pip install -r requirements.txt

4️⃣ Configure environment
 Create a .env file in the project root:

GMAIL_CLIENT_ID=your_client_id

GMAIL_CLIENT_SECRET=your_client_secret

MYSQL_HOST=localhost

MYSQL_USER=root

MYSQL_PASSWORD=yourpassword

MYSQL_DATABASE=email_sentiment

5️⃣ Start MySQL and Ollama
 Ensure MySQL is running locally
 Start Ollama and pull required models:

ollama pull gemma:2b

ollama pull yi:9b

6️⃣ Run email fetcher loop

python fetch_loop.py

7️⃣ Launch dashboard

python app.py

Dashboard will be available at: http://127.0.0.1:5000

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
📤 Email Routing Logic

Positive → Forward to positiveteam@example.com

Negative → Forward to negativeteam@example.com

Neutral → Forward to neutralteam@example.com

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
📜 License
This project is licensed under the Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0).
© 2025 Your Name. All rights reserved.




