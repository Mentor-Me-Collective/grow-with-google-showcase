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