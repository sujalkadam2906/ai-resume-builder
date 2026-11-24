# Setup and Installation Guide

**Project:** AI-Powered Resume Builder & Candidate Platform  
**Supported Platforms:** Windows 10/11, macOS, Linux (Ubuntu 20.04+)  
**Prerequisites:** Python 3.10+ (Python 3.13 tested), Node.js 18+ (Node 20+ recommended), Docker Desktop or Docker Engine  

---

## 1. Prerequisites Check

Verify your local development environment before installing:

```bash
# Verify Python version (3.10 or higher required)
python --version

# Verify Node.js and npm
node --version
npm --version

# Verify Docker and Docker Compose
docker --version
docker compose version
```

---

## 2. Clone Repository & Setup Virtual Environment

```bash
# Clone the repository
git clone https://github.com/sujalkadam2906/ai-resume-builder.git
cd ai-resume-builder

# Create a virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Windows (Command Prompt):
.venv\Scripts\activate.bat

# Linux / macOS:
source .venv/bin/activate
```

---

## 3. Install Backend Dependencies

Install the core Python resume engine and FastAPI backend packages:

```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies in editable development mode
pip install -e .

# Install web backend and database dependencies
pip install fastapi "uvicorn[standard]" "sqlalchemy>=2.0.0" "psycopg[binary]>=3.1.0" alembic pyjwt cryptography pytest httpx python-dotenv
```

---

## 4. Install Frontend Dependencies

```bash
# Navigate to frontend and install npm packages
cd frontend
npm install
cd ..
```

---

## 5. Environment Configuration

Copy the sanitized template to create your local `.env` file:

```bash
cp .env.example .env
```

For standard local development, the default values in `.env` are pre-configured:
```ini
APP_ENV=development
DEBUG=true
PORT=8000
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5434/resume_builder
REQUIRE_CF_ACCESS=false
ALLOW_DEV_AUTH_BYPASS=true
```

*(Optional)* Add your Google Gemini API key to `.env` to enable live AI rephrasing:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
```
*Note: If no API keys are provided, the platform automatically utilizes its built-in offline deterministic engine.*

---

## 6. Database Setup & Initialization

Start the PostgreSQL 16 container using Docker Compose:

```bash
# Start PostgreSQL service
docker compose up -d db

# Verify database health
docker compose ps
```

Run Alembic migrations to apply all 13 application tables:

```bash
# Run migrations to head
alembic upgrade head
```

Import candidate profiles into PostgreSQL:

```bash
# Ingest candidate profiles (demo_candidate and local profiles)
python -c "
from backend.app.database.session import SessionLocal
from backend.app.services.profile_ingestion import ProfileIngestionService

session = SessionLocal()
ingestion = ProfileIngestionService()
result = ingestion.import_all(session)
print('Ingestion Result:', result)
session.close()
"
```

---

## 7. Running the Application

### Start the FastAPI Backend:
In terminal 1 (with `.venv` active):
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base: `http://127.0.0.1:8000/api/v1`
- Interactive API Docs (Development only): `http://127.0.0.1:8000/docs`
- Health Probe: `http://127.0.0.1:8000/api/v1/health`

### Start the React Frontend:
In terminal 2:
```bash
cd frontend
npm run dev
```
- Web Application UI: `http://localhost:5173`

---

## 8. Verifying Installation & Running Tests

Run the complete regression test suite across the engine, backend, and security modules:

```bash
# Run all core engine tests (61 tests)
pytest tests/ -v

# Run all backend and security tests (69 tests)
pytest backend/tests/ -v

# Run frontend build check
npm --prefix frontend run build
```

---

## 9. Troubleshooting Common Issues

1. **Port 5434 Conflict:**
   If port 5434 is already in use by a local PostgreSQL service, change `POSTGRES_PORT` in your `.env` to `5435` and update the port binding in `docker-compose.yml`.
2. **Missing `pyjwt` or `cryptography`:**
   Run `pip install pyjwt cryptography` inside your active virtual environment.
3. **Database Migration Out of Sync:**
   Run `alembic current` to inspect migration revision. If needed, run `alembic stamp head` followed by `alembic upgrade head`.
