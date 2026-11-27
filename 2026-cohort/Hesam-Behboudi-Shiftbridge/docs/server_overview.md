# ShiftBridge API

ShiftBridge API is a FastAPI-based backend service designed for workforce shift management, scheduling conflict resolution, and AI-assisted shift rescheduling.

## Tech Stack
- **Framework:** FastAPI (v1.0.0)
- **Database:** SQLite (via SQLAlchemy ORM)
- **Authentication:** OAuth2 with Bearer JWT tokens
- **AI Integration:** Local AI engine with function-calling/tool execution

## Project Structure (Observed)
- `main.py` — Application entry point, database table initialization, CORS configuration, and router registration.
- `routes/auth.py` — User registration, login, and JWT authentication (`/auth`).
- `routes/chat.py` — AI chat interface and tool execution endpoints (`/chat`).
- `routes/shifts.py` — Data retrieval for projects, workers, shifts, scenarios, and shift proposal approvals (`/data`).

## CORS Configuration
The server is configured to allow credentials and all HTTP methods/headers from the following origins:
- `http://localhost:5173` (Local development UI)
- `http://ihesami.github.io/shiftBridge-UI` (Hosted UI)

## Running the Server
On startup, `main.py` automatically creates all SQLite tables defined in `Base.metadata`.

```bash
uvicorn main:app --reload
```

Once running, interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`