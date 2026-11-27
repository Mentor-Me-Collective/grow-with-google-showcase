# Configuration, Security & Schemas

## Environment Configuration (`config.py`)

Settings are managed using `pydantic_settings.BaseSettings` and automatically loaded from a `.env` file (UTF-8 encoded, extra keys ignored).

| Setting | Default Value | Description |
| :--- | :--- | :--- |
| `app_name` | `"FastAPI App"` | Application name |
| `debug_mode` | `False` | Debug mode toggle |
| `database_url` | `"sqlite:///./default.db"` | Database URL setting (note: `database.py` currently hardcodes `sqlite:///./shiftbridge.db`) |
| `secret_key` | `"default-secret-key"` | Secret key used for JWT signing |
| `local_llm_base_url` | `"http://172.17.0.1:8084"` | Base URL for the local OpenAI-compatible LLM server |
| `local_llm_api_key` | `"ollama"` | API key for the local LLM server |
| `local_llm_model` | `"qwen"` | Model identifier for chat completions |

---

## Security & Authentication (`security.py`)

- **Password Hashing:** Uses `passlib.context.CryptContext` with the `bcrypt` scheme (`verify_password`, `get_password_hash`).
- **JWT Tokens:** Uses `PyJWT` (`jwt.encode` / `jwt.decode`) with:
  - **Algorithm:** `HS256`
  - **Secret Key:** `settings.secret_key`
  - **Expiration:** `ACCESS_TOKEN_EXPIRE_MINUTES = 60`
  - **Payload:** Stores the user's email in the `"sub"` claim and expiration in `"exp"`.

---

## Pydantic Schemas (`schemas.py`)

Key request/response models used across the API:
- **Auth:** `UserCreate`, `UserLogin`, `UserResponse`, `Token`
- **Core Data:** `WorkerResponse`, `ShiftBase`, `ShiftCreate`, `ShiftResponse`, `ProjectBase`, `ProjectCreate`, `ProjectResponse`, `ScenarioResponse`
- **Proposals:** `ProposalResponse`, `ProposalApprovalRequest`, `ProposalApprovalResponse`, `RescheduleRequest`
- **Chat & Tools:** `ChatMessage`, `ChatRequest`, `ChatResponse`, `ChatMessageResponse`, `ToolExecutionRequest`, `ToolExecutionResponse`