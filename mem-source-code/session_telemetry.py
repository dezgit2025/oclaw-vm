"""
Session Telemetry Logger
========================
Wraps the ClawBot agentic loop to capture per-session metrics.
Drop this into your existing loop as a decorator/wrapper.

Logs to ~/.openclaw/logs/sessions/{session_id}.json
"""

import os
import json
import time
import uuid
import functools
from datetime import datetime
from typing import Any


LOGS_DIR = os.path.expanduser("~/.openclaw/logs/sessions")
os.makedirs(LOGS_DIR, exist_ok=True)


class SessionTelemetry:
    """Context manager that wraps an agentic loop session."""
    
    def __init__(self, model: str = "unknown", task_type: str = "general"):
        self.session_id = str(uuid.uuid4())[:8]
        self.model = model
        self.task_type = task_type
        self.start_time = None
        self.skill_invocations = []
        self.total_tokens_in = 0
        self.total_tokens_out = 0
        self.context_window_peak_pct = 0
        self.compaction_triggered = False
        self._current_skill = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._save()
        return False
    
    def start_skill(self, skill_name: str):
        """Call when a skill invocation begins."""
        self._current_skill = {
            "skill_name": skill_name,
            "start_time": time.time(),
            "tokens_in": 0,
            "tokens_out": 0,
            "tool_calls": 0,
            "retries": 0,
            "success": True,
            "error": None,
        }
    
    def end_skill(self, success=True, error=None):
        """Call when a skill invocation completes."""
        if self._current_skill:
            self._current_skill["latency_ms"] = int(
                (time.time() - self._current_skill.pop("start_time")) * 1000
            )
            self._current_skill["success"] = success
            self._current_skill["error"] = str(error) if error else None
            self.skill_invocations.append(self._current_skill)
            self._current_skill = None
    
    def record_api_call(self, tokens_in: int, tokens_out: int):
        """Record token usage from an API call."""
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out
        if self._current_skill:
            self._current_skill["tokens_in"] += tokens_in
            self._current_skill["tokens_out"] += tokens_out
    
    def record_tool_call(self):
        """Increment tool call counter for current skill."""
        if self._current_skill:
            self._current_skill["tool_calls"] += 1
    
    def record_retry(self):
        """Increment retry counter for current skill."""
        if self._current_skill:
            self._current_skill["retries"] += 1
    
    def record_context_usage(self, pct: float):
        """Track peak context window utilization."""
        self.context_window_peak_pct = max(self.context_window_peak_pct, pct)
    
    def _save(self):
        """Write session log to disk."""
        # Cost estimate (rough, Sonnet pricing)
        cost_per_1k_in = 0.003
        cost_per_1k_out = 0.015
        cost = (self.total_tokens_in / 1000 * cost_per_1k_in +
                self.total_tokens_out / 1000 * cost_per_1k_out)
        
        log = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(time.time() - self.start_time, 1),
            "model": self.model,
            "task_type": self.task_type,
            "skill_invocations": self.skill_invocations,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "total_tokens": self.total_tokens_in + self.total_tokens_out,
            "estimated_cost_usd": round(cost, 4),
            "context_window_peak_pct": self.context_window_peak_pct,
            "compaction_triggered": self.compaction_triggered,
        }
        
        path = os.path.join(LOGS_DIR, f"{self.session_id}.json")
        with open(path, "w") as f:
            json.dump(log, f, indent=2)


# ---------------------------------------------------------------------------
# Usage example with the agentic loop
# ---------------------------------------------------------------------------

def example_instrumented_loop():
    """
    Shows how to wrap your existing agentic loop with telemetry.
    
    Your actual loop probably looks like:
        while True:
            response = call_claude(messages)
            if stop_reason == "end_turn": break
            if stop_reason == "tool_use": execute tools, continue
    
    Add telemetry by wrapping it:
    """
    
    with SessionTelemetry(model="claude-sonnet-4-5", task_type="memory_extraction") as tel:
        
        messages = [{"role": "user", "content": "Extract facts from this conversation"}]
        
        for turn in range(20):  # max turns
            # Track which skill we're in
            tel.start_skill("memory_engine")
            
            # Your existing API call
            # response = client.messages.create(...)
            # tel.record_api_call(response.usage.input_tokens, response.usage.output_tokens)
            
            # For each tool call in the response
            # tel.record_tool_call()
            
            # If the tool call failed and retried
            # tel.record_retry()
            
            # When the skill invocation is done
            tel.end_skill(success=True)
            
            # Track context usage
            # tel.record_context_usage(response.usage.input_tokens / 200000 * 100)
            
            break  # demo
    
    print(f"Session logged: {tel.session_id}")
