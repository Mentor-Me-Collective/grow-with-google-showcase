
# ShiftBridge AI Service — Pipeline & Code Documentation

## Overview

`ai_service.py` implements `LocalLLMShiftAssistant`, a chat-based assistant that helps workers **view their shifts** and **create reschedule proposals**. It is designed around a **local, lower-capability LLM** accessed through the OpenAI-compatible API client, so the architecture deliberately offloads determinism to Python and keeps the model's role narrow.

The design principle is: **the model routes and phrases; Python verifies and executes.** No schedule fact ever originates from the model — every shift ID, date, and proposal status comes from a tool call whose result is captured verbatim.

---

## Architecture: The Three-Step Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                        chat(message, db, user)                  │
└─────────────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ STEP 1        │    │ STEP 2           │    │ STEP 3           │
│ Hint          │    │ Bounded Tool     │    │ Grounded Message │
│ Extraction    │───▶│ Loop             │───▶│ Formatting       │
│ (Python)      │    │ (LLM + tools)    │    │ (LLM + facts)    │
└───────────────┘    └──────────────────┘    └──────────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
  regex entities       tools_executed[]        final reply text
  (shift_id, length,   + created_proposal      grounded in
   date_str)                                      verified results
```

### Step 1 — Hint Extraction (deterministic, no LLM)

`extract_entities_fallback(text)` runs regexes over the user's raw message to pull out anything explicitly stated:

| Entity         | Pattern matched                 | Example input          |
| -------------- | ------------------------------- | ---------------------- |
| `shift_id`   | `shift (id\|#)? <num\|uuid>`    | "reschedule shift #42" |
| `project_id` | `project (id\|#)? <num\|uuid>`  | "project id 7"         |
| `length`     | `length/duration/for N hours` | "for 6 hours"          |
| `date_str`   | ISO-ish date/time               | "2025-03-14 09:00"     |

These hints are **injected into the user message** as a bracketed suffix:

```
reschedule shift 42

[Extracted hints from text: {"shift_id": "42"}]
```

This gives a weak model a second chance to notice explicit IDs it might otherwise drop. The hints are also used by `_normalize_tool_args` to backfill missing tool arguments.

> **Note:** Hints are appended to the message sent to the model only — `chat_history` passed by the caller is never mutated.

### Step 2 — Bounded Tool Loop

The model is called with `tools=tools.OPENAI_TOOLS` and `tool_choice="auto"`, up to `max_tool_steps` times (recommended: **5**). Each iteration:

1. Call the model.
2. If it returned `content`, save it as `draft_reply` (may be partial/inaccurate — used only as a phrasing hint later).
3. If no `tool_calls`, break.
4. For each tool call:
   - Parse arguments (`json.loads`, fall back to `{}` on error).
   - Normalize via `_normalize_tool_args` (backfill `shift_id`/`length` from hints; coerce `length` to float).
   - Execute via `tools.execute_tool_by_name(...)` with the DB session and current user ID.
   - Append `{tool, arguments, result}` to `tools_executed`.
   - If the tool was `create_reschedule_proposal` and succeeded, capture `created_proposal_data`.
   - Append a `role: "tool"` message so the model sees the result on the next turn.

The loop terminates on: no tool calls, step limit reached, or exception.

### Step 3 — Grounded Message Formatting

`_format_final_message` builds a **deterministic summary** of every tool result (`_build_verified_facts_summary`) and asks the model to rewrite it into a short user-facing reply, with strict rules:

- Only facts present in the verified summary.
- Explicitly say **"not completed"** if `create_reschedule_proposal` failed.
- No tool names, no JSON, no invented alternatives.
- 1–3 sentences.

If the formatter call fails or returns empty, the pipeline **falls back to the deterministic summary itself** — so the user always gets an accurate (if less polished) answer. If no tools ran at all, the cleaned `draft_reply` is returned directly.

---

## Return Contract

```python
{
    "reply": str,                    # final user-facing text
    "tools_used": [                  # audit trail, in execution order
        {"tool": str, "arguments": dict, "result": Any},
        ...
    ],
    "created_proposal": dict | None  # populated iff a proposal succeeded
}
```

On an unhandled exception the pipeline returns `{"reply": "Error", "tools_used": [], "created_proposal": None}` and logs the traceback.

---

## Prompt Design

### Tool Router Prompt (Step 2)

The router prompt must do four things a weak model cannot infer:

1. **State the capability gap** — "You do NOT know any schedules… You MUST call tools."
2. **Map intent → tool** — `get_my_shifts` for own shifts, `get_other_workers_shifts` for coverage/candidates, `create_reschedule_proposal` for the write.
3. **Prescribe the order** for a reschedule:
   - **A.** Resolve the shift (use provided `shift_id`, else `get_my_shifts`).
   - **B.** Optionally gather candidates (`get_other_workers_shifts`) if coverage is asked.
   - **C.** Call `create_reschedule_proposal` with the resolved `shift_id` and `length`.
   - **D.** Stop and summarize.
4. **Hard guards** — never invent IDs, never call the proposal tool without a `shift_id`, never repeat an identical call, no blind retries.

The full prompt is included in the code snippet below.

### Formatter Prompt (Step 3)

The formatter is domain-aware, not generic. It distinguishes three outcomes:

| Outcome                            | Instruction                                                                                            |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Proposal **succeeded**       | Confirm the reschedule, cite shift ID and proposal details from the summary.                           |
| Proposal **failed**          | Say the reschedule was **not completed**; give the reason from the results.                      |
| Tools only **gathered data** | Summarize findings; if a shift was identified but not rescheduled, ask the user to confirm the target. |
| **No shift identified**      | Say so; ask for the shift ID or date.                                                                  |

It is also told: no tool names, no JSON, no invented alternatives, 1–3 sentences, plain language.

---

## The Reschedule Workflow (end to end)

```
User: "Reschedule my 8-hour shift tomorrow to something else"
  │
  ├─ Step 1: hints = {"length": 8.0}   (no shift_id stated)
  │
  ├─ Step 2, iter 1: model calls get_my_shifts
  │     → result: [{"shift_id": 42, "date": "2025-03-14", "length": 8}, ...]
  │
  ├─ Step 2, iter 2: model calls get_other_workers_shifts (optional, if user asked about coverage)
  │     → result: candidate target shifts
  │
  ├─ Step 2, iter 3: model calls create_reschedule_proposal(shift_id=42, length=8)
  │     → result: {"success": true, "proposal": {...}}
  │
  ├─ Step 2, iter 4: model returns content, no tool calls → break
  │
  └─ Step 3: formatter sees SUCCEEDED → "Your 8-hour shift on 2025-03-14 (ID 42)
        has been submitted for reschedule. Proposal #... created."
```

---

## Configuration Knobs

| Setting               | Source                                                     | Default                               | Notes                               |
| --------------------- | ---------------------------------------------------------- | ------------------------------------- | ----------------------------------- |
| `base_url`          | `OPENAI_BASE_URL` env → `settings.local_llm_base_url` | —                                    | Local LLM endpoint                  |
| `api_key`           | `OPENAI_API_KEY` env → `settings.local_llm_api_key`   | —                                    | May be a dummy for local servers    |
| `model`             | `LOCAL_LLM_MODEL` env → `settings.local_llm_model`    | —                                    | Model name                          |
| `max_tool_steps`    | constructor                                                | 5 (recommended)                       | 3 is too tight for reschedule       |
| `max_history_turns` | constructor                                                | 8                                     | Trailing history turns replayed     |
| client timeout        | constructor                                                | `httpx.Timeout(215.0, connect=3.0)` | **Do not** use a 1.5s timeout |
| per-call timeout      | `chat()`                                                 | `httpx.Timeout(215.0, connect=3.0)` | Applied to each completion          |

### Timeout pitfall

The original code set `timeout=1.5` on the `OpenAI(...)` client while passing a 215s timeout per call. On a local model, the client-level 1.5s timeout preempts the per-call value and causes near-constant silent failures. **The client timeout must be ≥ the per-call timeout.**

---

## Helper Methods Reference

| Method                            | Role                                                                                                           |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `extract_entities_fallback`     | Regex entity extraction (shift_id, project_id, length, date_str).                                              |
| `_normalize_tool_args`          | Backfills `shift_id`/`length` from hints; coerces `length` to float.                                     |
| `_build_verified_facts_summary` | Deterministic, numbered summary of `tools_executed`; special-cases proposal success/failure and shift lists. |
| `_clean_model_text`             | Strips `<think>...</think>` blocks and whitespace.                                                           |
| `_format_final_message`         | Step 3 orchestration; returns model-formatted text or deterministic fallback.                                  |
| `chat`                          | Public entry point; runs Steps 1–3 and returns the result contract.                                           |

Module-level singleton: `ai_engine = LocalLLMShiftAssistant()`.

---

## Full Code

```python
import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from openai import OpenAI
from sqlalchemy.orm import Session

from config import settings
import models
import tools

logger = logging.getLogger(__name__)


class LocalLLMShiftAssistant:
    """Shift scheduling assistant powered by a local LLM via the OpenAI API client,
    using a multi-step flow (hint extraction -> bounded tool loop -> message formatting).
    """

    def __init__(self, max_tool_steps: int = 5, max_history_turns: int = 8):
        self.base_url = os.environ.get("OPENAI_BASE_URL", settings.local_llm_base_url)
        self.api_key = os.environ.get("OPENAI_API_KEY", settings.local_llm_api_key)
        self.model = os.environ.get("LOCAL_LLM_MODEL", settings.local_llm_model)
        self.max_tool_steps = max_tool_steps
        self.max_history_turns = max_history_turns
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            max_retries=0,
            timeout=httpx.Timeout(215.0, connect=3.0),
        )

    def extract_entities_fallback(self, text: str) -> Dict[str, Any]:
        """Heuristic entity extractor for explicit IDs, dates, and durations."""
        entities: Dict[str, Any] = {}

        shift_match = re.search(
            r"\bshift\s*(?:id|#)?\s*(\d+|[a-f0-9\-]{36})\b", text, re.IGNORECASE
        )
        if shift_match:
            entities["shift_id"] = shift_match.group(1)

        proj_match = re.search(
            r"\bproject\s*(?:id|#)?\s*(\d+|[a-f0-9\-]{36})\b", text, re.IGNORECASE
        )
        if proj_match:
            entities["project_id"] = proj_match.group(1)

        length_match = re.search(
            r"(?:length|duration|for)\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr|h)?\b",
            text,
            re.IGNORECASE,
        )
        if length_match:
            entities["length"] = float(length_match.group(1))

        # e.g. "8-hour shift", "8h shift", "8 hr shift"
        adhoc = re.search(
            r"\b(\d+(?:\.\d+)?)\s*[- ]?\s*(?:hour|hr|h)\s+shift\b", text, re.IGNORECASE
        )
        if adhoc and "length" not in entities:
            entities["length"] = float(adhoc.group(1))

        iso_match = re.search(
            r"\b(\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:[T\s]\d{1,2}:\d{2}(?::\d{2})?)?)\b",
            text,
        )
        if iso_match:
            entities["date_str"] = iso_match.group(1)

        return entities

    def _normalize_tool_args(
        self, fn_name: str, raw_args: Dict[str, Any], extracted_hints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Clean up common small-model argument issues before calling a tool."""
        args = dict(raw_args) if isinstance(raw_args, dict) else {}

        if "shift_id" not in args and "shift_id" in extracted_hints:
            args["shift_id"] = extracted_hints["shift_id"]

        if fn_name == "create_reschedule_proposal":
            if "length" in args and isinstance(args["length"], str):
                try:
                    args["length"] = float(args["length"])
                except ValueError:
                    pass
            elif "length" not in args and "length" in extracted_hints:
                args["length"] = extracted_hints["length"]

        return args

    def _build_verified_facts_summary(self, tools_executed: List[Dict[str, Any]]) -> str:
        """Create a deterministic, human-readable summary of executed tool results."""
        if not tools_executed:
            return "No database/schedule tools were called."

        sections: List[str] = []
        for idx, item in enumerate(tools_executed, start=1):
            tool_name = item.get("tool", "unknown_tool")
            res = item.get("result")

            if not isinstance(res, dict):
                sections.append(f"[{idx}] {tool_name}: {json.dumps(res)}")
                continue

            if tool_name == "create_reschedule_proposal":
                if res.get("success"):
                    proposal = res.get("proposal") or {}
                    sections.append(
                        f"[{idx}] create_reschedule_proposal SUCCEEDED: "
                        f"proposal={json.dumps(proposal)}"
                    )
                else:
                    sections.append(
                        f"[{idx}] create_reschedule_proposal FAILED: "
                        f"error={res.get('error') or res.get('message') or 'unknown error'}"
                    )
            elif tool_name in ("get_my_shifts", "get_other_workers_shifts"):
                shifts = res.get("shifts")
                if isinstance(shifts, list):
                    sections.append(
                        f"[{idx}] {tool_name} returned {len(shifts)} shift(s): "
                        f"{json.dumps(shifts)}"
                    )
                else:
                    sections.append(f"[{idx}] {tool_name}: {json.dumps(res)}")
            else:
                sections.append(f"[{idx}] {tool_name}: {json.dumps(res)}")

        return "\n".join(sections)

    def _clean_model_text(self, text: Optional[str]) -> str:
        """Remove reasoning tags or stray surrounding whitespace."""
        if not text:
            return ""
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
        return cleaned.strip()

    def _format_final_message(
        self,
        user_message: str,
        tools_executed: List[Dict[str, Any]],
        draft_reply: str,
        request_timeout: httpx.Timeout,
    ) -> str:
        """Step 3: Turn tool results (and any draft reply) into a concise, grounded message."""
        deterministic_summary = self._build_verified_facts_summary(tools_executed)

        if not tools_executed:
            cleaned_draft = self._clean_model_text(draft_reply)
            return cleaned_draft or "How can I help with your shifts or reschedule proposals?"

        formatter_system_prompt = (
            "You are the reply formatter for ShiftBridge Assistant.\n"
            "Write ONE short, friendly, factual reply to the user based ONLY on VERIFIED TOOL RESULTS.\n\n"
            "STRICT RULES:\n"
            "- Use ONLY facts present in VERIFIED TOOL RESULTS. Never invent shift IDs, dates, times, names, or statuses.\n"
            "- If create_reschedule_proposal SUCCEEDED: confirm the reschedule, state the shift ID and any proposal details shown.\n"
            "- If create_reschedule_proposal FAILED: clearly say the reschedule was NOT completed, and give the reason from the results.\n"
            "- If the tools only gathered data (no proposal was created): summarize what you found and, if a shift was identified but not yet rescheduled, ask the user to confirm the reschedule target.\n"
            "- If no shift could be identified: say so and ask the user for the shift ID or date.\n"
            "- Do NOT mention tool names, JSON, function calls, or internal steps.\n"
            "- Do NOT invent alternatives the tools did not return.\n"
            "- Keep it to 1–3 sentences. Use plain language."
        )

        formatter_user_prompt = (
            f"User message:\n{user_message}\n\n"
            f"VERIFIED TOOL RESULTS:\n{deterministic_summary}\n\n"
            f"Draft assistant note (may contain inaccuracies—verify against VERIFIED TOOL RESULTS):\n"
            f"{self._clean_model_text(draft_reply) or '(none)'}"
        )

        try:
            fmt_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": formatter_system_prompt},
                    {"role": "user", "content": formatter_user_prompt},
                ],
                timeout=request_timeout,
            )
            formatted = self._clean_model_text(fmt_response.choices[0].message.content)
            if formatted:
                return formatted
        except Exception as e:
            logger.warning("Formatter step failed (%s); falling back to deterministic summary.", str(e))

        return deterministic_summary

    def chat(
        self,
        message: str,
        db: Session,
        current_user: models.Worker,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Multi-step chat flow:
        1. Extract explicit entities as hints.
        2. Run a bounded tool-calling loop to gather data / create proposals.
        3. Format a grounded final message from verified tool results.
        """
        tool_system_prompt = (
            f"You are ShiftBridge Assistant, a shift-scheduling tool router.\n"
            f"Current worker: ID={current_user.id}, Email={current_user.email}, Name={current_user.name}.\n"
            f"Reference timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\n\n"
            "YOUR JOB:\n"
            "You do NOT know any schedules, shift IDs, worker names, or availability. "
            "You MUST call tools to get that data. Never invent or guess IDs, dates, or names.\n\n"
            "AVAILABLE TOOLS AND WHEN TO USE THEM:\n"
            "1. `get_my_shifts`\n"
            "   - Use when the user refers to 'my shift', 'my shifts', or asks to reschedule/cancel/change one of their shifts.\n"
            "   - If the user did not provide an explicit shift_id, call this FIRST to find the shift they mean.\n"
            "   - If multiple shifts match, pick the one whose date/time best matches the user's description.\n"
            "2. `get_other_workers_shifts`\n"
            "   - Use when the user asks who is working, or when you need to find a target shift/slot to move the user's shift INTO.\n"
            "   - For a reschedule request, call this AFTER `get_my_shifts` if you need to identify candidate target shifts.\n"
            "3. `create_reschedule_proposal`\n"
            "   - Use ONLY when the user wants to reschedule a shift AND you have a concrete `shift_id` for that shift.\n"
            "   - Pass `shift_id` (the shift being moved) and `length` (duration in hours if known).\n"
            "   - Do NOT call this if you are missing the shift_id — call `get_my_shifts` first.\n\n"
            "RESCHEDULE WORKFLOW (follow this order):\n"
            "Step A. Identify the user's shift:\n"
            "   - If shift_id was provided in the message, use it.\n"
            "   - Otherwise call `get_my_shifts` and select the matching shift.\n"
            "Step B. (Only if the user asks about coverage/swap/who can take it) "
            "call `get_other_workers_shifts` to gather candidates.\n"
            "Step C. Call `create_reschedule_proposal` with the resolved shift_id and length.\n"
            "Step D. Stop calling tools. Summarize what you did.\n\n"
            "RULES:\n"
            "- Never call the same tool twice with identical arguments.\n"
            "- Never call `create_reschedule_proposal` without a valid shift_id.\n"
            "- If a tool returns an error, do not retry blindly — report it.\n"
            "- After at most one create_reschedule_proposal attempt, stop and report the outcome."
        )

        # Step 1: Extract explicit hints from the current message without mutating caller history
        extracted_hints = self.extract_entities_fallback(message)
        enriched_user_message = message
        if extracted_hints:
            enriched_user_message = (
                f"{message}\n\n[Extracted hints from text: {json.dumps(extracted_hints)}]"
            )

        messages: List[Dict[str, Any]] = [{"role": "system", "content": tool_system_prompt}]
        if chat_history:
            for turn in chat_history[-self.max_history_turns :]:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                if role in ("user", "assistant", "system") and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": enriched_user_message})

        request_timeout = httpx.Timeout(215.0, connect=3.0)

        try:
            tools_executed: List[Dict[str, Any]] = []
            created_proposal_data: Optional[Dict[str, Any]] = None
            draft_reply = ""

            # Step 2: Bounded multi-step tool loop
            for _step in range(self.max_tool_steps):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools.OPENAI_TOOLS,
                    tool_choice="auto",
                    timeout=request_timeout,
                )

                assistant_msg = response.choices[0].message
                if assistant_msg.content:
                    draft_reply = assistant_msg.content

                if not assistant_msg.tool_calls:
                    break

                messages.append(assistant_msg)

                for tool_call in assistant_msg.tool_calls:
                    fn_name = tool_call.function.name
                    try:
                        raw_args = json.loads(tool_call.function.arguments or "{}")
                    except Exception as e:
                        logger.warning("Failed to parse tool arguments for %s: %s", fn_name, str(e))
                        raw_args = {}

                    fn_args = self._normalize_tool_args(fn_name, raw_args, extracted_hints)

                    tool_result = tools.execute_tool_by_name(
                        tool_name=fn_name,
                        args=fn_args,
                        db=db,
                        current_user_id=current_user.id,
                    )

                    tools_executed.append(
                        {
                            "tool": fn_name,
                            "arguments": fn_args,
                            "result": tool_result,
                        }
                    )

                    if fn_name == "create_reschedule_proposal" and isinstance(tool_result, dict):
                        if tool_result.get("success") and tool_result.get("proposal"):
                            created_proposal_data = tool_result.get("proposal")

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result),
                        }
                    )

            # Step 3: Format final user-facing message grounded in tool results
            final_reply = self._format_final_message(
                user_message=message,
                tools_executed=tools_executed,
                draft_reply=draft_reply,
                request_timeout=request_timeout,
            )

            return {
                "reply": final_reply,
                "tools_used": tools_executed,
                "created_proposal": created_proposal_data,
            }

        except Exception as e:
            logger.exception("Local LLM pipeline failed: %s", str(e))
            return {
                "reply": "Error",
                "tools_used": [],
                "created_proposal": None,
            }


ai_engine = LocalLLMShiftAssistant()
```

---

## Known Pitfalls & Mitigations

| Pitfall                             | Symptom                                      | Mitigation                                                                                                  |
| ----------------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Model hallucinates `shift_id`     | Proposal fails with "shift not found"        | Prompt forbids it; `_normalize_tool_args` backfills from regex hints; formatter reports failure honestly. |
| Tool loop exhausted before proposal | User gets "gathered data" reply, no proposal | `max_tool_steps=5` gives room for resolve → gather → propose → summarize.                              |
| 1.5s client timeout                 | Sporadic `Error` replies on local model    | Client timeout set to `215s` matching per-call timeout.                                                   |
| Formatter model failure             | Empty or garbled reply                       | Falls back to `_build_verified_facts_summary` deterministic text.                                         |
| Repeated identical tool calls       | Loop spins without progress                  | Prompt rule: "Never call the same tool twice with identical arguments."                                     |
| `<think>` tags leaking to user    | Internal reasoning visible                   | `_clean_model_text` strips them at both draft and format stages.                                          |
| History mutation                    | Caller's `chat_history` corrupted          | Only a sliced copy is read; hints are appended to the local `messages` list.                              |
