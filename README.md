📧 Email Sentiment Analysis Dashboard
A Flask-based web application that fetches emails from a Gmail inbox, analyzes their sentiment using a local Ollama model, and displays them in an interactive dashboard.

✨ Features
📩 Fetch Unread Emails from Gmail using the Gmail API

🧠 Sentiment Analysis with Ollama (Positive, Negative, Neutral)

📊 Categorized Dashboard for quick sentiment-based viewing

🔄 Refresh Button to fetch new unread emails instantly

💾 Local Database Storage for saving email records

🛠️ Tech Stack
Component	Technology Used
Backend	Flask (Python)
Frontend	HTML, CSS, JavaScript
Database	SQLite
API	Gmail API
AI Model	Ollama

📂 Project Structure
bash
Copy
Edit
Email-Sentiment/
│── static/css/           # Stylesheets
│── templates/            # HTML Templates
│── app.py                 # Main Flask App
│── db_utils.py            # Database Helper Functions
│── email_utils.py         # Email Processing Functions
│── fetch_emails.py        # Email Fetching Logic
│── gmail_auth.py          # Gmail Authentication
│── init_db.py             # Database Initialization
│── ollama_utils.py        # Ollama Sentiment Analysis
│── emails.db              # SQLite Database
│── README.md              # Documentation
🚀 Getting Started
1️⃣ Clone the repository
bash
Copy
Edit
git clone https://github.com/ArunNamagiri/Email-Sentiment.git
cd Email-Sentiment
2️⃣ Install dependencies
bash
Copy
Edit
pip install -r requirements.txt
3️⃣ Configure Gmail API
Enable the Gmail API in Google Cloud Console

Download credentials.json and place it in the project root

4️⃣ Run the app
bash
Copy
Edit
python app.py
Visit http://127.0.0.1:5000/ in your browser.

📸 Screenshots
Dashboard View	Sentiment Categories

📜 License
This project is licensed under the MIT License.

