# CIE Evaluator

AI-assisted Cambridge International Examinations (CIE) answer evaluation system.

Upload past exam papers and mark schemes, answer each question, and receive instant AI grading based strictly on the mark scheme — just like a Cambridge head examiner.

---

## Features

- **Email authentication** with verification flow
- **PDF upload** for question papers and mark schemes
- **Automatic parsing** of Cambridge question hierarchy (Q1, Q1(a), Q1(a)(i), …)
- **Mark scheme matching** for each sub-question
- **AI grading** using OpenAI GPT-4o or Anthropic Claude
- **Per-question AI chat** with three modes: feedback, improve answer, model answer
- **Diagram upload** support (up to 3 per question)
- **Dashboard** with subject filtering

---

## Tech Stack

| Layer      | Technology |
|------------|------------|
| Frontend   | React + Vite + Tailwind CSS + React Query + Zustand |
| Backend    | FastAPI + Python 3.11 |
| Database   | PostgreSQL + SQLAlchemy + Alembic |
| PDF Parse  | pdfplumber |
| AI         | OpenAI GPT-4o / Anthropic Claude |
| Auth       | JWT (access + refresh tokens) + bcrypt |

---

## Quick Start (Docker)

### 1. Clone the repo

```bash
git clone https://github.com/yourname/cie-evaluator.git
cd cie-evaluator
```

### 2. Configure backend environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set:

```env
OPENAI_API_KEY=sk-your-key-here
# or
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here

SMTP_USER=your@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Start all services

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

---

## Local Development (without Docker)

### Backend

```bash
cd backend

# Create virtualenv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install deps
pip install -r requirements.txt

# Copy and configure env
cp .env.example .env
# Edit .env with your DB and API keys

# Run database migrations (first time)
python -c "from app.database import engine, Base; from app.models.models import *; Base.metadata.create_all(bind=engine)"

# Start the server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

npm install
npm run dev
# → http://localhost:3000
```

### PostgreSQL (local)

```bash
# macOS
brew install postgresql
brew services start postgresql
createdb cie_evaluator
createuser cie_user
psql -c "ALTER USER cie_user WITH PASSWORD 'cie_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE cie_evaluator TO cie_user;"

# Or via Docker only for DB
docker run -d \
  --name cie-postgres \
  -e POSTGRES_DB=cie_evaluator \
  -e POSTGRES_USER=cie_user \
  -e POSTGRES_PASSWORD=cie_password \
  -p 5432:5432 \
  postgres:16-alpine
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://cie_user:cie_password@localhost:5432/cie_evaluator` | PostgreSQL connection string |
| `SECRET_KEY` | `change-me` | JWT signing secret (use `openssl rand -hex 32`) |
| `AI_PROVIDER` | `openai` | `openai` or `anthropic` |
| `AI_MODEL` | `gpt-4o` | Model to use for grading |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | — | Email address |
| `SMTP_PASSWORD` | — | App password (not account password) |
| `FRONTEND_URL` | `http://localhost:3000` | Used in verification emails |
| `MAX_FILE_SIZE_MB` | `50` | Max PDF upload size |

---

## API Endpoints

### Authentication

```
POST /auth/register        Register new account
POST /auth/login           Login and get JWT tokens
POST /auth/verify-email    Verify email token
POST /auth/refresh         Refresh access token
GET  /auth/me              Get current user
POST /auth/logout          Invalidate refresh token
```

### Papers

```
POST /papers/upload        Upload question paper + mark scheme
GET  /papers               List user's papers (filterable)
GET  /papers/{id}          Get paper details
DELETE /papers/{id}        Delete paper
```

### Questions

```
GET /questions/paper/{paper_id}   Get all parsed questions for a paper
```

### Answers

```
POST /answers/submit                      Submit and grade an answer
POST /answers/chat                        Chat with AI about an answer
GET  /answers/question/{question_id}      Get existing answer
POST /answers/upload-image/{question_id}  Upload diagram image
```

---

## PDF Requirements

Upload **text-based PDFs** only. These are PDFs where you can select and copy text in your PDF viewer.

Recommended sources:
- [PapaCambridge](https://papacambridge.com)
- [GCE Guide](https://gceguide.com)
- [SaveMyExams](https://www.savemyexams.co.uk)

Do **not** upload scanned image PDFs — text extraction will fail.

---

## Project Structure

```
cie-evaluator/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings management
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── models/
│   │   │   └── models.py        # ORM models: User, Paper, Question, StudentAnswer
│   │   ├── schemas/
│   │   │   └── schemas.py       # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── auth.py          # Auth endpoints
│   │   │   ├── papers.py        # Paper upload + management
│   │   │   ├── questions.py     # Question listing
│   │   │   └── answers.py       # Answer submit + AI chat
│   │   ├── services/
│   │   │   ├── pdf_parser.py    # PDF text extraction + structure parsing
│   │   │   ├── ai_grader.py     # AI grading + chat service
│   │   │   └── email_service.py # SMTP email verification
│   │   └── utils/
│   │       └── auth.py          # JWT + bcrypt utilities
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Router setup
│   │   ├── main.jsx             # React entry point
│   │   ├── index.css            # Tailwind + global styles
│   │   ├── store/
│   │   │   └── authStore.js     # Zustand auth state
│   │   ├── services/
│   │   │   └── api.js           # Axios API client
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   ├── VerifyEmailPage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── UploadPaperPage.jsx
│   │   │   └── PaperPage.jsx
│   │   └── components/
│   │       ├── Layout.jsx
│   │       ├── QuestionCard.jsx
│   │       └── AIChatPanel.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
└── docker-compose.yml
```

---

## Development Notes

### Email in Development

If SMTP is not configured, verification links are logged to the backend console:

```
INFO: DEV - Verification URL: http://localhost:3000/verify-email?token=abc123
```

Copy this URL into your browser to verify your account without configuring SMTP.

### AI Cost Control

- AI is called **only** when a student submits an answer or sends a chat message.
- PDF parsing uses **deterministic regex** — no AI involved.
- Chat history is limited to the **last 6 messages** per context window.

### Adding Alembic Migrations

```bash
cd backend
alembic init migrations
# Edit alembic.ini: sqlalchemy.url = your DATABASE_URL
# Edit migrations/env.py: import your models and set target_metadata

alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

## License

MIT
