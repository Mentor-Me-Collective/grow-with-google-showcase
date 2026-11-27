# Architecture & Core Workflows

## 1. Authentication Flow
1. A user registers via `POST /auth/signup` or logs in via `POST /auth/login`.
2. Passwords are hashed and verified using `security.py`.
3. On login, a JWT token is issued with the user's email stored in the `sub` claim.
4. Protected routes use the `get_current_user` dependency (`OAuth2PasswordBearer`), which decodes the JWT, extracts the email, and fetches the corresponding `Worker` record from SQLite.

## 2. AI Chat & Tool Execution
- The `/chat` router acts as a bridge between the frontend, the database, and `ai_engine`.
- When a user sends a message to `POST /chat`, the server passes the `message`, `db` session, `current_user`, and `chat_history` to `ai_engine.chat()`.
- Tools can be inspected via `GET /chat/tools` and manually/programmatically invoked via `POST /chat/tools/execute`, which delegates to `tools.execute_tool_by_name()`.

## 3. Dual-Approval Shift Proposal Workflow
Shift modifications proposed by workers or the AI follow a two-party approval process via `POST /data/approve`:

1. **Authorization Check:**
   - If the current user is the proposal's `worker_id`, `isWorkerApproved` is set to `True`.
   - If the current user has `is_manager=True` and manages a project that the proposal's worker is assigned to, `isManagerApproved` is set to `True`.
   - Otherwise, a `403 Forbidden` error is raised.

2. **Partial Approval:**
   - If only one party has approved, the proposal is saved and returned with `"deleted": false`.

3. **Full Approval (Both Worker & Manager):**
   - The `new_shift_data` payload is extracted and normalized (`proposed_day` → `day`, `proposed_start_time` → `start_time`, `proposed_length` → `length`).
   - If `shift_id` matches an existing `Shift`, that shift is updated; otherwise, a new `Shift` record is created.
   - The `Proposal` record is deleted from the database, and the response returns `"deleted": true` along with the updated/created `new_shift`.
