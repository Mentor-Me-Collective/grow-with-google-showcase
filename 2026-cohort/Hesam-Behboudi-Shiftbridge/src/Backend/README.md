# ShiftBridge API

ShiftBridge is a modern shift and project management API built with **FastAPI**, **SQLAlchemy**, and an **AI assistant powered by local LLMs via the OpenAI API** standard (such as Ollama, LM Studio, vLLM, or LocalAI).

Workers can chat with the local AI model to view coworker schedules, inspect their own shifts, and reschedule their shifts with automated conflict checking.

---

## Features

- **Authentication & Security**: Secure user signup, login, and profile access using JWT Bearer tokens and bcrypt password hashing.
- **Projects & Shifts Models**:
  - `Project`: Tracks project title, manager (`manager_id` foreign key), and assigned workers (many-to-many relationship).
  - `Shift`: Tracks project association (`project_id`), worker ownership (`owner_id`), `start_date`, and duration (`length`).
- **Local AI Agent via OpenAI API**:
  - Connects to any OpenAI-compatible local model server (e.g., Ollama at `http://localhost:11434/v1` or custom host).
  - Uses OpenAI function calling / tools to inspect coworker shifts and execute shift reschedules directly against the database.
  - Built-in resilient fallback engine to ensure offline continuity and instant test execution.
- **Data Seeding**: Instant database seeding script generating 1 manager, 15 worker accounts, 1 project, and staggered shifts.

---

## Tech Stack

- **Framework**: FastAPI
- **Database / ORM**: SQLite & SQLAlchemy 2.0
- **Validation**: Pydantic v2
- **AI / LLM Integration**: `openai` Python SDK (OpenAI-compatible local LLM endpoint with Tool Calling)
- **Testing**: Pytest & Starlette TestClient

---

## Getting Started

### 1. Prerequisites

- Python 3.10 or higher
- (Optional) Local LLM runner such as [Ollama](https://ollama.com/), [LM Studio](https://lmstudio.ai/), or vLLM.

### 2. Clone & Setup Virtual Environment

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

Install all required packages using `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Configuration

Create or modify your `.env` file in the root directory (refer to `.env.example`):

```ini
APP_NAME="ShiftBridge API"
DEBUG_MODE=true
DATABASE_URL="sqlite:///./shiftbridge.db"
SECRET_KEY="your-secure-jwt-secret-key"

# Local LLM settings (OpenAI-compatible endpoint)
LOCAL_LLM_BASE_URL="http://localhost:11434/v1"
LOCAL_LLM_API_KEY="ollama"
LOCAL_LLM_MODEL="llama3.2"
```

> **Note on Local LLMs**:
> If you are using Ollama, ensure your model is pulled:
>
> ```bash
> ollama pull llama3.2
> # or
> ollama pull qwen2.5
> ```

---

## Database Seeding

To seed the database with **1 manager**, **15 workers in one project**, and **15 upcoming scheduled shifts**, run:

```bash
python seed.py
```

### Sample Seeded Credentials

| Role                | Email                        | Password        | Details                        |
| ------------------- | ---------------------------- | --------------- | ------------------------------ |
| **Manager**   | `manager@shiftbridge.com`  | `password123` | Sarah Connor (Project Manager) |
| **Worker 1**  | `worker1@shiftbridge.com`  | `password123` | Alex Morgan                    |
| **Worker 2**  | `worker2@shiftbridge.com`  | `password123` | Brian Davis                    |
| ...                 | ...                          | ...             | ...                            |
| **Worker 15** | `worker15@shiftbridge.com` | `password123` | Olivia Martinez                |

To reset and re-seed the database:

```bash
python seed.py --reset
```

---

## Running the Application

Start the FastAPI application with Uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Once running:

- **API Root**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Running Automated Tests

Run the full test suite using `pytest`:

```bash
pytest
```

Run tests with verbose output:

```bash
pytest -v
```

The test suite covers:

- User signup, duplicate validation, login, and JWT authentication (`tests/test_auth.py`)
- Project and Shift model creation, many-to-many worker assignment, relationships, and cascading deletes (`tests/test_models.py`)
- AI Chat endpoints, OpenAI tool calling round-trip, multi-turn reschedule, and direct shift APIs (`tests/test_chat_and_tools.py`)
- Data seeding script verification and idempotency (`tests/test_seed.py`)

---

## API Endpoints Overview

### Authentication (`/auth`)

- `POST /auth/signup` - Register a new worker account
- `POST /auth/login` - Authenticate and receive a JWT Bearer access token
- `GET /auth/me` - Retrieve current authenticated user profile

### AI Chat & Tools (`/chat`)

- `POST /chat` - Natural language chat with the local LLM to reschedule shifts or inspect coworker schedules
  ```json
  {
    "message": "Can you show me other workers' shifts and reschedule my shift on project 1 to 2026-11-20 09:00?",
    "history": []
  }
  ```
- `GET /chat/tools` - Exposes OpenAI-compatible tool schemas (`get_other_workers_shifts`, `reschedule_shift`, `get_my_shifts`)
- `POST /chat/tools/execute` - Directly invoke a tool by name with arguments

### Shifts (`/shifts`)

- `GET /shifts/my-shifts` - List current user's shifts
- `GET /shifts/project/{project_id}/workers` - List other workers' shifts in a project
- `PATCH /shifts/{shift_id}/reschedule` - Directly reschedule a shift



# Deploying ShiftBridge to Google Cloud Run

This section explains how to deploy the ShiftBridge API to **Google Cloud Run** using the provided `Dockerfile`.

---

## Cloud Run Deployment

### 1. Prerequisites

- A Google Cloud project with billing enabled
- [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install) installed and authenticated
- Docker installed locally (optional, for local image testing)
- Enable the required APIs:

```bash
gcloud services enable run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

### 2. How the Dockerfile Fits Cloud Run

The provided `Dockerfile` is already Cloud Run–ready:

| Dockerfile Instruction                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Why It Matters on Cloud Run                                                                              |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `FROM python:3.12-slim`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Lightweight base image reduces cold-start time and image size.                                           |
| `WORKDIR /app` + `COPY requirements.txt` first                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Leverages Docker layer caching so dependency installs are only re-run when `requirements.txt` changes. |
| `RUN pip install --no-cache-dir -r requirements.txt`                                                                                                                                                                                                                                                                                                                                                                                                                                                            | `--no-cache-dir` keeps the image small (no pip cache layer).                                           |
| `RUN useradd --create-home --uid 10001 appuser` + `USER appuser`                                                                                                                                                                                                                                                                                                                                                                                                                                              | Runs the container as a non-root user — a Cloud Run security best practice.                             |
| `CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1` | **Critical:** Cloud Run injects a `PORT` environment variable at runtime. The shell form expands `${PORT}`, and `exec` ensures Uvicorn receives `SIGTERM` directly for graceful shutdown during scale-down. Binding to `0.0.0.0` is required so Cloud Run's front end can reach the container. `--workers 1` is recommended because Cloud Run scales horizontally by container instances, not worker processes. |                                                                                                          |

> **Note on SQLite:** Cloud Run containers have an **ephemeral filesystem**. The default `DATABASE_URL="sqlite:///./shiftbridge.db"` will not persist across revisions or instances. For production, switch to a managed database (e.g., Cloud SQL for PostgreSQL) and update `DATABASE_URL` accordingly. For a quick demo, the in-container SQLite file works but resets on each new instance.

### 3. Configure Environment Variables

Cloud Run does not read your local `.env` file. Pass configuration via `--set-env-vars` or `--set-secrets`:

```bash
# Minimum required runtime variables
gcloud run deploy shiftbridge-api \
  --set-env-vars="APP_NAME=ShiftBridge API,DEBUG_MODE=false,DATABASE_URL=sqlite:///./shiftbridge.db,LOCAL_LLM_BASE_URL=http://localhost:11434/v1,LOCAL_LLM_MODEL=llama3.2"
```

For sensitive values such as `SECRET_KEY` and `LOCAL_LLM_API_KEY`, use **Secret Manager** instead of plain env vars:

```bash
# Store the secret
echo -n "your-secure-jwt-secret-key" | \
  gcloud secrets create SHIFTBRIDGE_SECRET_KEY --data-file=-

# Grant the Cloud Run service account access
gcloud secrets add-iam-policy-binding SHIFTBRIDGE_SECRET_KEY \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Reference it at deploy time
gcloud run deploy shiftbridge-api \
  --set-secrets="SECRET_KEY=SHIFTBRIDGE_SECRET_KEY:latest"
```

> **Local LLM caveat:** `LOCAL_LLM_BASE_URL="http://localhost:11434/v1"` points to Ollama running on the *same machine*. On Cloud Run, `localhost` refers to the container itself, so the LLM endpoint will be unreachable. Options:
>
> - Deploy your LLM (e.g., vLLM on a Cloud Run GPU service or GKE) and set `LOCAL_LLM_BASE_URL` to its URL.
> - Rely on the built-in **resilient fallback engine** described in the README, which keeps chat endpoints functional when the LLM is unavailable.

### 4. Build & Deploy

#### Option A — Deploy from source (Cloud Build builds the image for you)

Run from the repository root containing the `Dockerfile`:

```bash
gcloud run deploy shiftbridge-api \
  --source . \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=8080 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --timeout=300
```

- `--source .` triggers Cloud Build to build the `Dockerfile` and push to Artifact Registry automatically.
- `--allow-unauthenticated` makes the API publicly reachable (remove for private/internal APIs and use IAM).
- `--min-instances=0` allows scale-to-zero (cold starts may occur; set to `1` to keep it warm).
- `--port=8080` matches the `PORT` default in the Dockerfile; Cloud Run overrides it via the `${PORT}` expansion.
- `--timeout=300` allows up to 5 minutes per request — useful if the local LLM call is slow.

#### Option B — Build with Docker, push to Artifact Registry, then deploy

```bash
# 1. Create a repository (one-time)
gcloud artifacts repositories create shiftbridge \
  --repository-format=docker \
  --location=us-central1

# 2. Authenticate Docker to Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# 3. Build and push
export IMAGE=us-central1-docker.pkg.dev/PROJECT_ID/shiftbridge/api:latest
docker build -t $IMAGE .
docker push $IMAGE

# 4. Deploy
gcloud run deploy shiftbridge-api \
  --image=$IMAGE \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=8080
```

### 5. Run Database Seeding (Optional, Demo Only)

Because the container filesystem is ephemeral, seeding must happen at runtime. Two approaches:

1. **Seed on container start** — add a startup command that runs `python seed.py` before Uvicorn (e.g., override `CMD` with a small entrypoint script). Be aware this re-seeds on every cold start.
2. **Use a persistent database** — migrate to Cloud SQL, then run `python seed.py` once from a Cloud Run Job or a temporary VM pointed at the same `DATABASE_URL`.

Example Cloud Run Job for seeding against Cloud SQL:

```bash
gcloud run jobs create shiftbridge-seed \
  --image=$IMAGE \
  --region=us-central1 \
  --set-env-vars="DATABASE_URL=postgresql+psycopg://user:pass@/shiftbridge?host=/cloudsql/PROJECT_ID:us-central1:shiftbridge-db" \
  --set-cloudsql-instances=PROJECT_ID:us-central1:shiftbridge-db \
  --command="python" --args="seed.py"

gcloud run jobs execute shiftbridge-seed --region=us-central1
```

### 6. Verify the Deployment

```bash
# Get the service URL
gcloud run services describe shiftbridge-api \
  --region=us-central1 \
  --format='value(status.url)'
```

Then check:

- `GET https://YOUR_SERVICE_URL/` — API root
- `GET https://YOUR_SERVICE_URL/docs` — Swagger UI
- `POST https://YOUR_SERVICE_URL/auth/login` with seeded credentials (if seeded)

View logs:

```bash
gcloud run services logs read shiftbridge-api --region=us-central1
```

### 7. Updating the Service

Re-run the deploy command after code changes. Cloud Run creates a new revision, shifts traffic, and keeps the previous revision available for rollback:

```bash
gcloud run deploy shiftbridge-api --source . --region=us-central1

# Roll back to a prior revision if needed
gcloud run services update-traffic shiftbridge-api \
  --region=us-central1 \
  --to-revisions=shiftbridge-api-00001-abc=100
```

### 8. Production Checklist

- [ ] Replace SQLite with Cloud SQL (PostgreSQL) and update `DATABASE_URL`
- [ ] Store `SECRET_KEY` and `LOCAL_LLM_API_KEY` in Secret Manager
- [ ] Set `DEBUG_MODE=false` in production
- [ ] Point `LOCAL_LLM_BASE_URL` at a reachable LLM service (or accept fallback behavior)
- [ ] Configure a dedicated service account with least-privilege IAM
- [ ] Add `--min-instances=1` if cold starts are unacceptable
- [ ] Enable Cloud Run health checks / readiness if adding long LLM timeouts
- [ ] Set up Cloud Monitoring alerts on 5xx rates and latency
