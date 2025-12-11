
###  Timesheet Tracking Bot with LLM-powered extraction & smart clarification

This project is a **fully asynchronous, production-grade Timesheet Bot** built for **Microsoft Teams**.  
It handles **natural-language task logging**, **onboarding**, **authentication**, **invite-based registration**, and **PostgreSQL-backed timesheet storage**, all powered using OpenAI’s LLM.

---

## 🚀 Features

### ✔ Human-like Timesheet Logging

Users can describe work naturally:

`today morning worked 3h fixing backend api issues yesterday completed deployment 5 hours`

The bot intelligently extracts:

- **date** (relative or absolute)
    
- **project**
    
- **task description**
    
- **task type**
    
- **hours worked**
    

It detects missing or unclear information and asks for clarifications.

---

### ✔ Smart Clarification Flow

If the user forgets something:

- **Missing project?** → Bot asks:  
    _“Which project was this for?”_
    
- **Unclear task type?** → Bot asks:  
    _“Was this development, testing, debugging, or something else?”_
    
- **No description?** →  
    _“Tell me a bit about what you worked on 😊”_
    
- **Unknown project but previously used one?**  
    _“Should I log this under your last project ‘Glovatrix’? (yes/no)”_
    

---

### ✔ Secure Authentication

- Username + password (bcrypt-hashed)
    
- New users onboard via **invite codes**
    
- Per-user session state stored in DB
    
- Persistent login tied to Teams user external_id
    

---

### ✔ Correction System

Users can modify previous logs:

`update last to 3h correct last 2.5 h`

Updates the **latest entry** in database.

---

### ✔ Clean, maintainable folder structure

```
timesheet-bot/
│
├── bot/
│   ├── app/
│   │   ├── main.py              ← Bot entrypoint (aiohttp)
│   │   ├── router.py            ← Message routing
│   │   ├── auth_flow.py         ← Login & onboarding logic
│   │   ├── timesheet_flow.py    ← Timesheet handling, clarifications, saving
│   │
│   ├── db/
│   │   ├── pool.py              ← Async Postgres pool
│   │   ├── sessions.py          ← Conversation/user sessions
│   │   ├── users.py             ← User CRUD + bcrypt
│   │   ├── invites.py           ← Invite code system
│   │   ├── timesheet.py         ← Insert/update timesheet records
│   │
│   ├── nlp/
│   │   ├── extract.py           ← LLM extraction engine
│   │
│   ├── texts/
│   │   ├── responses.py         ← Bot response templates
│   │
│   ├── logging.py               ← Structured logging
│   ├── config.py                ← Env var loader
│
├── scripts/
│   ├── init_db.py               ← DB initialization + seed users/invites
│
├── requirements.txt
├── README.md
└── .env.example

```

---

## 🛠 Tech Stack

### **Backend**

- **Python 3.10+**
    
- **aiohttp** (fully async web server)
    
- **asyncpg** (high-performance PostgreSQL driver)
    
- **Bot Framework SDK** (MS Teams integration)
    

### **AI / NLP**

- **OpenAI GPT-4o-mini** (natural language extraction)
    
- LangChain wrapper for async usage
    

### **Database**

- PostgreSQL
    
- Tables auto-created via schema bootstrap
    

### **Security**

- bcrypt password hashing
    
- Invite-code-based onboarding
    
- Per-user session state control
    

---

## 📦 Installation & Setup

### 1️⃣ Clone the repo

`git clone <repo-url> cd timesheet-bot`

---

### 2️⃣ Create virtual environment

`python -m venv .venv source .venv/bin/activate   # Windows: .venv\Scripts\activate`

---

### 3️⃣ Install dependencies

`pip install -r requirements.txt`

---

### 4️⃣ Setup environment variables

`cp .env.example .env`

Set:

```
BOT_APP_ID=<teams-app-id>
BOT_APP_PASSWORD=<teams-app-password>
POSTGRES_DSN=postgresql://postgres:root@localhost:5432/MSBot
OPENAI_API_KEY=<your-openai-api-key>
```

---

### 5️⃣ Start PostgreSQL

If using Docker:

`docker-compose up -d postgres`

Or use local PG instance.

---

### 6️⃣ Initialize database

`python -m bot.scripts.init_db`

This creates:

- tables
    
- initial invite codes
    
- seed user (`adhish / Timesheet@123`)
    

---

### 7️⃣ Run bot

`python -m bot.app.main`

You’ll see:

`Bot listening on http://localhost:3978/api/messages`

Open **Bot Framework Emulator**, connect:

`http://localhost:3978/api/messages`

---

## 💬 Example Conversation

**User:** hi  
**Bot:** Hey! What’s your username?

**User:** adhish  
**Bot:** Please enter your password ✨

**User:** Timesheet@123  
**Bot:**  
“Welcome back Adhish! What did you work on today?”

---

**User:** yesterday worked 3h fixing some backend api stuff  
**Bot:**  
“Which project was this for?”

**User:** Glovatrix  
**Bot:**  
“Was this development, testing, debugging or something else?”

**User:** development  
**Bot:**  
“Great! Logging this entry:  
✔ 3h — Development — fixing backend api — Glovatrix  
Save it? (yes/no)”

**User:** yes  
**Bot:**  
“Done! Logged successfully 🎉”

---

## 📈 Why This Bot Is Production-Ready

- Fully async (aiohttp + asyncpg)
    
- High throughput suitable for large orgs
    
- Session-driven conversation flow
    
- Handles ambiguous or incomplete inputs gracefully
    
- Secure onboarding (invite + bcrypt)
    
- Modular architecture for future expansion
    

---

## 📌 Upcoming Enhancements

- User analytics dashboards
    
- Personal productivity insights
    
- More advanced correction history
    
- Project-based time summaries
    
- Integration with JIRA / Azure DevOps
    

---

## 🤝 Contributing

Pull requests are welcome!  
If you'd like new features or deeper LLM logic—open an issue.