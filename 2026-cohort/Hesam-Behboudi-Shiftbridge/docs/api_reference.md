# ShiftBridge API Reference

## Health Check
### `GET /`
Returns the service health status.
- **Response:** `{"status": "healthy", "service": "ShiftBridge API"}`

---

## Authentication (`/auth`)

### `POST /auth/signup`
Registers a new worker account with default role `"Staff"`, department `"General"`, and `is_manager=False`.
- **Request Body:** `UserCreate` (`email`, `password`, `full_name`)
- **Response (`201 Created`):** `UserResponse`
- **Errors:** `400 Bad Request` if the email is already registered.

### `POST /auth/login`
Authenticates a worker and returns a JWT access token.
- **Request Body:** `UserLogin` (`username` [email], `password`)
- **Response:** `Token` (`access_token`, `token_type: "bearer"`)
- **Errors:** `401 Unauthorized` if credentials are invalid.

### `GET /auth/me`
Returns the profile of the currently authenticated user.
- **Auth:** Bearer Token required.
- **Response:** `UserResponse`

---

## AI Chat & Tools (`/chat`)
*All endpoints in this group require Bearer Token authentication.*

### `POST /chat`
Sends a message (and optional conversation history) to the local AI model to inspect schedules or reschedule shifts.
- **Request Body:** `ChatRequest` (`message`, optional `history`)
- **Response:** `ChatResponse`

### `GET /chat/tools`
Exposes the list of available tool definitions (`tools.AVAILABLE_TOOLS`) for function calling.
- **Response:** `{"tools": [...]}`

### `POST /chat/tools/execute`
Executes a specific AI tool by name with the provided arguments.
- **Request Body:** `ToolExecutionRequest` (`tool_name`, `arguments`)
- **Response:** `ToolExecutionResponse` (`success`, `result`)

---

## Data & Shifts (`/data`)

### `GET /data/projects`
Retrieves all projects, including assigned workers and manager details.
- **Response:** `List[ProjectResponse]`

### `GET /data/projects/{project_id}`
Retrieves a specific project by ID.
- **Response:** `ProjectResponse`
- **Errors:** `404 Not Found` if the project does not exist.

### `GET /data/workers`
Retrieves all workers.
- **Auth:** Bearer Token required.
- **Response:** `List[WorkerResponse]`

### `GET /data/shifts`
Retrieves all scheduled shifts, with an optional `project_id` query filter.
- **Query Params:** `project_id` (optional)
- **Response:** `List[ShiftResponse]`

### `GET /data/scenarios`
Retrieves all scheduling conflict scenarios.
- **Response:** `List[ScenarioResponse]`

### `GET /data/proposals`
Retrieves shift change proposals.
- **Auth:** Bearer Token required.
- **Behavior:**
  - **Managers** (`is_manager=True`): Returns proposals for all workers in projects they manage.
  - **Workers:** Returns only proposals belonging to the logged-in worker.
- **Response:** `List[ProposalResponse]`

### `POST /data/approve`
Approves a shift change proposal as either the assigned worker or their supervising manager.
- **Auth:** Bearer Token required.
- **Request Body:** `ProposalApprovalRequest` (`proposal_id`)
- **Response:** `ProposalApprovalResponse`
- **Errors:** `404 Not Found` if proposal doesn't exist; `403 Forbidden` if user is not the assigned worker or supervising manager.