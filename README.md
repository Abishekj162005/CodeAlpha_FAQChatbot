# FAQBot — NLP-Based Question Answering System

FAQBot is a modern, lightweight NLP-powered FAQ chatbot application built using **Python, Flask, NLTK, Scikit-learn (TF-IDF & Cosine Similarity), SQLite**, and a **SaaS-grade responsive HTML5/CSS3/JavaScript frontend**.

---

## 🌟 Features

* **Natural Language Processing**: Lowercasing, punctuation stripping, tokenization, stop-words removal, and lemmatization using NLTK.
* **TF-IDF & Cosine Similarity Engine**: Vectorizes FAQ entries and user queries to compute exact and semantic relevance scores.
* **Configurable Similarity Threshold**: Ensures accurate answers and returns polite fallback responses for out-of-domain questions (Threshold default: `0.40`).
* **SaaS-Grade Modern UI**: Clean layout, glassmorphism headers, smooth bubble animations, copy-to-clipboard buttons, and typing indicators.
* **Interactive Quick Suggestions**: Pre-populated suggestion chips for instant answers.
* **Light / Dark Mode**: Theme toggle with preference persisted in `localStorage`.
* **Voice Capabilities**: Web Speech API for voice question input and Speech Synthesis for text-to-speech reading.
* **User Feedback Mechanism**: Thumbs up / thumbs down helpfulness ratings recorded in SQLite.
* **Admin Knowledge Base Dashboard**: Modal UI for real-time CRUD operations (Add, Edit, Delete FAQs & Filter by category).

---

## 📁 Project Structure

```text
FAQ-Chatbot/
│
├── app.py                   # Main Flask application & REST endpoints
├── requirements.txt         # Python package dependencies
├── .env                     # Environment configuration
├── .env.example             # Template for environment configuration
├── .gitignore               # Files excluded from git
├── README.md                # Project documentation
│
├── data/
│   └── faqs.json            # Seed FAQ dataset
│
├── database/
│   └── faq.db               # SQLite database (auto-generated)
│
├── templates/
│   └── index.html           # Main chatbot HTML interface
│
├── static/
│   ├── css/
│   │   └── style.css        # Responsive SaaS stylesheet
│   └── js/
│       └── script.js        # Asynchronous frontend controller & speech logic
│
├── utils/
│   ├── __init__.py
│   ├── preprocessing.py    # NLP text preprocessing pipeline
│   ├── similarity.py       # TF-IDF + Cosine Similarity matcher
│   └── db_helper.py        # SQLAlchemy models & database helpers
│
└── tests/
    └── test_nlp.py          # Unit test suite for NLP logic
```

---

## 🚀 Quick Start Guide

### Prerequisites
* Python 3.8 or higher installed on your system.

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-username/codealpha-FAQchatbot.git
cd codealpha-FAQchatbot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

Open your browser and navigate to `http://127.0.0.1:5000`.

---

## 🧪 Running Unit Tests

To run the automated NLP pipeline and similarity matcher test suite:

```bash
python -m unittest discover -s tests
```

---

## 🛰️ REST API Endpoints

### 1. Ask Question
* **Endpoint:** `POST /ask`
* **Request:** `{"question": "How do I reset my password?"}`
* **Response:**
  ```json
  {
    "status": "success",
    "question": "How do I reset my password?",
    "answer": "You can reset your password by clicking 'Forgot Password' on the login page...",
    "matched": true,
    "similarity": 0.9412,
    "suggestions": ["How do I update my profile information?"]
  }
  ```

### 2. Get All FAQs
* **Endpoint:** `GET /api/faqs`

### 3. Add New FAQ (Admin)
* **Endpoint:** `POST /api/faqs`
* **Request:** `{"category": "Account", "question": "...", "answer": "..."}`

### 4. Record Feedback
* **Endpoint:** `POST /api/feedback`
* **Request:** `{"question": "...", "helpful": true, "faq_id": 1}`

---

## ⚙️ Configuration

Create or modify `.env` in the root directory:

```env
FLASK_ENV=development
PORT=5000
SECRET_KEY=faqbot-secret-key
SIMILARITY_THRESHOLD=0.40
DATABASE_URI=sqlite:///database/faq.db
```

---

## 📄 License
Distributed under the MIT License.
