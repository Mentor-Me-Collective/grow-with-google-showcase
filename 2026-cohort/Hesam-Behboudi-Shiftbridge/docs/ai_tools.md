# AI Assistant & Tool-Calling Engine

ShiftBridge integrates a local LLM via an OpenAI-compatible client (`ai_service.py`) and exposes database-backed function-calling tools (`tools.py`).

## `LocalLLMShiftAssistant` (`ai_service.py`)

- **Client Configuration:** Uses the `openai.OpenAI` client pointed at `settings.local_llm_base_url` (default: `http://172.17.0.1:8084`) with `settings.local_llm_api_key` and `settings.local_llm_model` (default: `qwen`). Environment variables `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `LOCAL_LLM_MODEL` override these defaults.
- **Timeouts:**
  - Client initialization: `max_retries=0`, `timeout=1.5`
  - Chat completion requests: `httpx.Timeout(215.0, connect=3.0)`
- **Chat Flow (`ai_engine.chat`):**
  1. Builds a system prompt containing the authenticated worker's `id`, `email`, `name`, and current timestamp.
  2. Appends optional `chat_history` and the new `message`.
  3. Sends the request with `tools=tools.OPENAI_TOOLS` and `tool_choice="auto"`.
  4. If the model returns `tool_calls`, executes each tool via `tools.execute_tool_by_name()`, appends the JSON results as `role: "tool"` messages, and performs a second completion call to generate the final natural-language reply.
  5. Returns `{"reply": ..., "tools_used": [...], "created_proposal": ...}`.
- **Error Handling:** If the local LLM is unreachable or fails, `chat()` logs the error and returns `{"reply": "Error", "tools_used": [], "created_proposal": None}`. A helper `extract_entities_fallback()` is also defined for regex-based extraction of `shift_id`, `project_id`, `length`, and `date_str`.

---

## Available Tools (`tools.py`)

Tools are defined in `AVAILABLE_TOOLS` and formatted for OpenAI function calling in `OPENAI_TOOLS`.

### 1. `get_other_workers_shifts`

Fetches shifts of coworkers to check availability and avoid scheduling conflicts.

- **Parameters:**
  - `project_id` (`string`, optional): Filter by a specific project. If omitted, retrieves coworker shifts across all projects the current user belongs to.
- **Returns:** `{"success": True, "count": int, "shifts": [...]}`

### 2. `get_my_shifts`

Fetches all scheduled shifts belonging to the currently authenticated worker.

- **Parameters:**
  - `project_id` (`string`, optional): Accepted in schema (currently queries all shifts for `current_user_id`).
- **Returns:** `{"success": True, "count": int, "shifts": [...]}`

### 3. `create_reschedule_proposal`

Creates a new `Proposal` record in the database for one of the current user's shifts.

- **Parameters:**
  - `shift_id` (`string`, required): ID of the shift to reschedule (must belong to `current_user_id`).
  - `day` (`string`, required): Proposed day of the week (e.g., `'Monday'`).
  - `start_time` (`string`, required): Proposed start time (e.g., `'07:00'`).
  - `length` (`number`, required): Proposed shift duration in hours (e.g., `8.0`).
  - `note` (`string`, optional): Reason or note for the reschedule.
- **Behavior:** Stores both current and proposed shift fields inside `Proposal.new_shift_data` with `isManagerApproved=False` and `isWorkerApproved=False`.
- **Returns:** `{"success": True, "message": "...", "proposal": {...}}` or `{"success": False, "error": "..."}` if the shift is not found.
