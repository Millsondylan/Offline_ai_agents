"""Real-time thinking logger for capturing and displaying model activity."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


class ThinkingLogger:
    """Logs model thinking, reasoning, and actions in real-time."""

    def __init__(self, state_root: Path):
        self.state_root = state_root
        self.thinking_file = state_root / "thinking.jsonl"
        self.current_cycle: Optional[int] = None
        self._ensure_state_dir()

    def _ensure_state_dir(self) -> None:
        """Ensure state directory exists."""
        self.state_root.mkdir(parents=True, exist_ok=True)

    def start_cycle(self, cycle_num: int) -> None:
        """Start a new cycle."""
        self.current_cycle = cycle_num
        self.log_event("cycle_start", {
            "cycle": cycle_num,
            "message": f"Starting cycle {cycle_num}"
        })

    def log_thinking(self, thought_type: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a thinking event.

        Args:
            thought_type: Type of thought (planning, reasoning, decision, action, etc.)
            content: The thought content
            metadata: Optional additional data
        """
        self.log_event("thinking", {
            "type": thought_type,
            "content": content,
            "metadata": metadata or {},
        })

    def log_action(self, action: str, details: str, status: str = "started") -> None:
        """Log an action being taken.

        Args:
            action: Action name
            details: Action details
            status: started, completed, failed
        """
        self.log_event("action", {
            "action": action,
            "details": details,
            "status": status,
        })

    def log_analysis(self, subject: str, analysis: str, file_path: Optional[str] = None) -> None:
        """Log code/data analysis.

        Args:
            subject: What is being analyzed
            analysis: Analysis content
            file_path: Optional file path being analyzed
        """
        self.log_event("analysis", {
            "subject": subject,
            "analysis": analysis,
            "file_path": file_path,
        })

    def log_decision(self, decision: str, rationale: str, alternatives: Optional[list] = None) -> None:
        """Log a decision being made.

        Args:
            decision: The decision made
            rationale: Why this decision was made
            alternatives: Other options considered
        """
        self.log_event("decision", {
            "decision": decision,
            "rationale": rationale,
            "alternatives": alternatives or [],
        })

    def log_verification(self, check_name: str, passed: bool, message: str) -> None:
        """Log a verification check result.

        Args:
            check_name: Name of the check
            passed: Whether it passed
            message: Result message
        """
        self.log_event("verification", {
            "check": check_name,
            "passed": passed,
            "message": message,
        })

    def log_model_interaction(self, prompt_summary: str, response_summary: str,
                             prompt_tokens: Optional[int] = None,
                             response_tokens: Optional[int] = None) -> None:
        """Log model API interaction.

        Args:
            prompt_summary: Summary of prompt sent
            response_summary: Summary of response received
            prompt_tokens: Token count for prompt
            response_tokens: Token count for response
        """
        self.log_event("model_interaction", {
            "prompt_summary": prompt_summary,
            "response_summary": response_summary,
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
        })

    def log_code_generation(self, file_path: str, operation: str, lines_changed: int) -> None:
        """Log code generation activity.

        Args:
            file_path: File being modified
            operation: create, modify, delete
            lines_changed: Number of lines changed
        """
        self.log_event("code_generation", {
            "file_path": file_path,
            "operation": operation,
            "lines_changed": lines_changed,
        })

    def log_error(self, error_type: str, message: str, details: Optional[Dict] = None) -> None:
        """Log an error.

        Args:
            error_type: Type of error
            message: Error message
            details: Additional error details
        """
        self.log_event("error", {
            "error_type": error_type,
            "message": message,
            "details": details or {},
        })

    def log_strategy(self, strategy: str, steps: list, expected_outcome: str) -> None:
        """Log a strategic plan.

        Args:
            strategy: Strategy being employed
            steps: Steps to execute
            expected_outcome: Expected result
        """
        self.log_event("strategy", {
            "strategy": strategy,
            "steps": steps,
            "expected_outcome": expected_outcome,
        })

    def log_reflection(self, reflection: str, learned: str, next_action: str) -> None:
        """Log a reflection on previous actions.

        Args:
            reflection: Reflection on what happened
            learned: What was learned
            next_action: What to do next
        """
        self.log_event("reflection", {
            "reflection": reflection,
            "learned": learned,
            "next_action": next_action,
        })

    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log a generic event.

        Args:
            event_type: Type of event
            data: Event data
        """
        event = {
            "timestamp": time.time(),
            "cycle": self.current_cycle,
            "event_type": event_type,
            "data": data,
        }

        # Append to JSONL file
        with open(self.thinking_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def get_recent_events(self, limit: int = 50, event_types: Optional[list] = None) -> list:
        """Get recent thinking events.

        Args:
            limit: Maximum events to return
            event_types: Filter by event types

        Returns:
            List of recent events
        """
        if not self.thinking_file.exists():
            return []

        events = []
        with open(self.thinking_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event_types is None or event.get("event_type") in event_types:
                        events.append(event)
                except json.JSONDecodeError:
                    continue

        # Return most recent
        return events[-limit:]

    def get_cycle_events(self, cycle_num: int) -> list:
        """Get all events for a specific cycle.

        Args:
            cycle_num: Cycle number

        Returns:
            List of events for that cycle
        """
        if not self.thinking_file.exists():
            return []

        events = []
        with open(self.thinking_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event.get("cycle") == cycle_num:
                        events.append(event)
                except json.JSONDecodeError:
                    continue

        return events

    def clear_history(self) -> None:
        """Clear thinking history."""
        if self.thinking_file.exists():
            self.thinking_file.unlink()
