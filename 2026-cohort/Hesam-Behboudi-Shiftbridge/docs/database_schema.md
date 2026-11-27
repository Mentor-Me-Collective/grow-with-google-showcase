# ShiftBridge Database Schema

The application uses **SQLAlchemy 2.0** with a **SQLite** database (`sqlite:///./shiftbridge.db`) configured in `database.py`. Tables are automatically created on startup via `Base.metadata.create_all(bind=engine)` in `main.py`.

## Entity-Relationship Overview

- **Workers & Projects (Many-to-Many):** Linked via the `project_workers` association table.
- **Manager & Projects (One-to-Many):** A `Worker` can manage multiple `Project` records (`Project.manager_id`).
- **Project & Shifts (One-to-Many):** A `Project` has many `Shift` records.
- **Worker & Shifts (One-to-Many):** A `Worker` has many `Shift` records.
- **Worker & Proposals (One-to-Many):** A `Worker` can have multiple `Proposal` records.

---

## Tables

### `project_workers` (Association Table)
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `project_id` | `String` | Primary Key, Foreign Key (`projects.id`, `ON DELETE CASCADE`) |
| `worker_id` | `String` | Primary Key, Foreign Key (`workers.id`, `ON DELETE CASCADE`) |

### `projects`
| Column | Type | Constraints / Default | Description |
| :--- | :--- | :--- | :--- |
| `id` | `String` | Primary Key, Indexed | Unique project identifier |
| `manager_id` | `String` | Foreign Key (`workers.id`, `ON DELETE CASCADE`), Not Null | ID of the managing worker |
| `title` | `String` | Not Null, Indexed | Project title |
| `created_at` | `DateTime` | Default: `datetime.now` | Creation timestamp |

### `workers`
| Column | Type | Constraints / Default | Description |
| :--- | :--- | :--- | :--- |
| `id` | `String` | Primary Key, Indexed | Unique worker identifier |
| `email` | `String` | Unique, Indexed, Not Null | Worker email address (used for login) |
| `hashed_password` | `String` | Not Null | Bcrypt-hashed password |
| `name` | `String` | Not Null | Full name |
| `role` | `String` | Not Null | e.g., `'Senior RN'`, `'Charge Nurse'`, `'RN'`, `'LPN'`, `'Support Specialist'`, `'Project Manager'` |
| `department` | `String` | Not Null | Department name |
| `max_hours` | `Float` | Not Null, Default: `40.0` | Maximum weekly hours |
| `current_hours` | `Float` | Not Null, Default: `0.0` | Currently assigned hours |
| `avatar` | `String` | Nullable | Optional avatar URL/path |
| `is_manager` | `Boolean` | Not Null, Default: `False` | Whether the worker has manager privileges |

### `shifts`
| Column | Type | Constraints / Default | Description |
| :--- | :--- | :--- | :--- |
| `id` | `String` | Primary Key, Indexed | Unique shift identifier |
| `project_id` | `String` | Foreign Key (`projects.id`, `ON DELETE CASCADE`), Not Null | Associated project |
| `worker_id` | `String` | Foreign Key (`workers.id`, `ON DELETE CASCADE`), Not Null | Assigned worker |
| `day` | `String` | Not Null | Day of the week (`'Monday'` – `'Sunday'`) |
| `type` | `String` | Not Null, Default: `"regular"` | `'regular'`, `'conflict'`, `'updated'`, or `'off'` |
| `start_time` | `String` | Not Null | Shift start time (e.g., `'07:00'`) |
| `length` | `Float` | Not Null | Shift duration in hours |
| `note` | `String` | Nullable | Optional shift note |
| `updated_by_ai` | `Boolean` | Default: `False` | Flag indicating AI modification |
| `conflict_reason` | `String` | Nullable | Description of scheduling conflict, if any |

### `proposals`
| Column | Type | Constraints / Default | Description |
| :--- | :--- | :--- | :--- |
| `id` | `String` | Primary Key, Indexed | Unique proposal UUID |
| `worker_id` | `String` | Foreign Key (`workers.id`, `ON DELETE CASCADE`), Not Null | Worker requesting/receiving the change |
| `new_shift_data` | `JSON` | Nullable | JSON payload containing current and proposed shift details |
| `isManagerApproved` | `Boolean` | Default: `False` | Manager approval status |
| `isWorkerApproved` | `Boolean` | Default: `False` | Worker approval status |

### `chat_messages`
| Column | Type | Constraints / Default | Description |
| :--- | :--- | :--- | :--- |
| `id` | `String` | Primary Key, Indexed | Unique message ID |
| `sender` | `String` | Not Null | `'user'`, `'assistant'`, or `'system'` |
| `role_name` | `String` | Nullable | Display role name |
| `text` | `String` | Not Null | Message content |
| `timestamp` | `String` | Not Null | Message timestamp |
| `is_pending_approval` | `Boolean` | Nullable | Indicates if message awaits approval |
| `proposal_id` | `String` | Nullable | Associated proposal ID |
| `options` | `JSON` | Nullable | Interactive options payload |
| `approval_state` | `JSON` | Nullable | Approval state metadata |