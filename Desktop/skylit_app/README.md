# Skylit Logistics (Phase 1 scaffold)

This workspace contains a scaffold for the AI-powered Logistics Operations & Inventory System.

Backend (FastAPI)
- Location: `backend/`
- Run with Docker Compose: `docker-compose up --build`

Notes:
- Populate `backend/.env` with your secrets (API_KEY, WHATSAPP_TOKEN, GEMINI_API_KEY).
- The FastAPI webhook at `/webhook` is a minimal handler; extend `gemini_service.py` with real Gemini SDK calls.

Environment variables
- `GEMINI_API_KEY`: API key for Google Gemini (used by `app/gemini_service.py`)
- `WHATSAPP_TOKEN`: Meta WhatsApp API token used to send messages
- `WHATSAPP_VERIFY_TOKEN`: verification token for webhook setup
- `PHONE_ID` / `WHATSAPP_PHONE_NUMBER_ID`: Meta phone number id for sending messages
- `DATABASE_URL`: SQLAlchemy database URL (defaults to `sqlite:///./test.db`)

Running tests
- Install dev deps: `pip install -r backend/requirements.txt`
- Run tests from the `backend` directory: `pytest -q`

Postgres + pgAdmin (Docker)

- The repository includes a Postgres service in `docker-compose.yml`. To add pgAdmin for a web UI we added a `pgadmin` service.
- Start services:

```bash
docker-compose up -d
```

- Access pgAdmin at: http://localhost:8080
	- Email: `admin@skylit.local`
	- Password: `admin`

- To connect to the Postgres server from pgAdmin use:
	- Host: `db`
	- Port: `5432`
	- Username: `skylit`
	- Password: `skylitpass`
	- Database: `skylitdb`

Note: For production, change the default pgAdmin credentials and secure Docker volumes.
