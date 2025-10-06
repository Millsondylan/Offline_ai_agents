"""Agent communication and control."""

import logging
import queue
import threading
import time
from collections import deque
from datetime import datetime
from typing import Any, Callable, Deque, List, Optional

from agent_control_panel.core.models import (
    AgentState,
    AgentStatus,
    LogEntry,
    Thought,
)


logger = logging.getLogger(__name__)


class AgentController:
    """Controls and communicates with the autonomous agent."""

    def __init__(
        self,
        max_thought_queue: int = 1000,
        max_log_queue: int = 5000,
        connection_timeout: float = 5.0,
        auto_reconnect: bool = False,
    ):
        """Initialize agent controller.

        Args:
            max_thought_queue: Maximum thoughts to queue
            max_log_queue: Maximum logs to queue
            connection_timeout: Timeout for connection attempts
            auto_reconnect: Whether to auto-reconnect on disconnect
        """
        self.max_thought_queue = max_thought_queue
        self.max_log_queue = max_log_queue
        self.connection_timeout = connection_timeout
        self.auto_reconnect = auto_reconnect

        # Agent state
        self._state = AgentState.IDLE
        self._current_cycle = 0
        self._total_cycles = 0
        self._session_start: Optional[float] = None
        self._last_error: Optional[str] = None
        self._is_paused = False
        self._is_connected = False
        self._is_reconnecting = False

        # Message queues
        self._thought_queue: Deque[Thought] = deque(maxlen=max_thought_queue)
        self._log_queue: Deque[LogEntry] = deque(maxlen=max_log_queue)

        # Subscribers
        self._thought_subscribers: List[Callable[[Thought], None]] = []
        self._log_subscribers: List[Callable[[LogEntry], None]] = []

        # Background tasks
        self._background_threads: List[threading.Thread] = []
        self._shutdown_event = threading.Event()

        # Metrics
        self._thoughts_count = 0
        self._actions_count = 0

        # Thread safety
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the agent."""
        with self._lock:
            if self._state == AgentState.RUNNING:
                logger.warning("Agent already running")
                return

            self._state = AgentState.RUNNING
            self._session_start = time.time()
            self._is_connected = True
            logger.info("Agent started")

    def pause(self) -> None:
        """Pause the agent."""
        with self._lock:
            if self._state != AgentState.RUNNING:
                logger.warning("Cannot pause non-running agent")
                return

            self._state = AgentState.PAUSED
            self._is_paused = True
            logger.info("Agent paused")

    def resume(self) -> None:
        """Resume the agent."""
        with self._lock:
            if not self._is_paused:
                logger.warning("Agent not paused")
                return

            self._state = AgentState.RUNNING
            self._is_paused = False
            logger.info("Agent resumed")

    def stop(self) -> None:
        """Stop the agent."""
        with self._lock:
            self._state = AgentState.STOPPED
            self._is_connected = False
            logger.info("Agent stopped")

    def is_running(self) -> bool:
        """Check if agent is running.

        Returns:
            True if agent is running
        """
        with self._lock:
            return self._state == AgentState.RUNNING

    def is_paused(self) -> bool:
        """Check if agent is paused.

        Returns:
            True if agent is paused
        """
        with self._lock:
            return self._is_paused

    def is_connected(self) -> bool:
        """Check if connected to agent.

        Returns:
            True if connected
        """
        with self._lock:
            return self._is_connected

    def is_reconnecting(self) -> bool:
        """Check if currently attempting reconnection.

        Returns:
            True if reconnecting
        """
        with self._lock:
            return self._is_reconnecting

    def get_status(self) -> AgentStatus:
        """Get current agent status.

        Returns:
            Current agent status
        """
        with self._lock:
            duration = (
                time.time() - self._session_start
                if self._session_start
                else 0.0
            )

            return AgentStatus(
                state=self._state,
                current_cycle=self._current_cycle,
                total_cycles=self._total_cycles,
                model_name="gpt-4",  # Would come from agent
                provider="openai",    # Would come from agent
                session_duration_seconds=duration,
                last_error=self._last_error,
                thoughts_count=self._thoughts_count,
                actions_count=self._actions_count,
            )

    def subscribe_thoughts(self, callback: Callable[[Thought], None]) -> None:
        """Subscribe to agent thoughts.

        Args:
            callback: Function to call with each thought
        """
        with self._lock:
            self._thought_subscribers.append(callback)
            logger.debug("Added thought subscriber")

    def subscribe_logs(self, callback: Callable[[LogEntry], None]) -> None:
        """Subscribe to agent logs.

        Args:
            callback: Function to call with each log entry
        """
        with self._lock:
            self._log_subscribers.append(callback)
            logger.debug("Added log subscriber")

    def get_pending_thoughts(self) -> List[Thought]:
        """Get all pending thoughts.

        Returns:
            List of pending thoughts
        """
        with self._lock:
            return list(self._thought_queue)

    def get_pending_logs(self) -> List[LogEntry]:
        """Get all pending logs.

        Returns:
            List of pending log entries
        """
        with self._lock:
            return list(self._log_queue)

    def _emit_thought(self, thought: Thought) -> None:
        """Emit a thought to subscribers.

        Args:
            thought: Thought to emit
        """
        with self._lock:
            self._thought_queue.append(thought)
            self._thoughts_count += 1

            for subscriber in self._thought_subscribers:
                try:
                    subscriber(thought)
                except Exception as e:
                    logger.error(f"Error in thought subscriber: {e}")

    def _emit_log(self, log: LogEntry) -> None:
        """Emit a log entry to subscribers.

        Args:
            log: Log entry to emit
        """
        with self._lock:
            self._log_queue.append(log)

            for subscriber in self._log_subscribers:
                try:
                    subscriber(log)
                except Exception as e:
                    logger.error(f"Error in log subscriber: {e}")

    def _simulate_crash(self) -> None:
        """Simulate agent crash (for testing)."""
        with self._lock:
            self._state = AgentState.ERROR
            self._last_error = "Simulated crash"
            self._is_connected = False
            logger.error("Simulated agent crash")

    def _simulate_disconnect(self) -> None:
        """Simulate connection loss (for testing)."""
        with self._lock:
            self._is_connected = False

            if self.auto_reconnect:
                self._is_reconnecting = True
                # Would start reconnection thread

    def _simulate_cycle_complete(self) -> None:
        """Simulate completion of an agent cycle (for testing)."""
        with self._lock:
            self._current_cycle += 1
            self._actions_count += 1

    def _simulate_error(self, error: str) -> None:
        """Simulate an agent error (for testing).

        Args:
            error: Error message
        """
        with self._lock:
            self._state = AgentState.ERROR
            self._last_error = error

    def recover(self) -> None:
        """Attempt to recover from error state."""
        with self._lock:
            if self._state == AgentState.ERROR:
                self._state = AgentState.IDLE
                self._last_error = None
                logger.info("Agent recovered from error")

    def register_async_handler(self, handler: Callable) -> None:
        """Register async event handler.

        Args:
            handler: Async handler function
        """
        # In real implementation, would manage async event loop
        pass

    async def emit_event(self, event: str) -> None:
        """Emit an async event.

        Args:
            event: Event name
        """
        # In real implementation, would dispatch to async handlers
        pass

    def shutdown(self) -> None:
        """Shutdown controller and cleanup resources."""
        with self._lock:
            self._shutdown_event.set()
            self.stop()

            # Stop background threads
            for thread in self._background_threads:
                if thread.is_alive():
                    thread.join(timeout=1.0)

            logger.info("Agent controller shutdown complete")

    def _background_tasks_stopped(self) -> bool:
        """Check if all background tasks have stopped.

        Returns:
            True if all tasks stopped
        """
        return all(not t.is_alive() for t in self._background_threads)

    def connect_to_nonexistent_agent(self) -> bool:
        """Attempt to connect to nonexistent agent (for testing).

        Returns:
            False (connection fails)
        """
        time.sleep(self.connection_timeout)
        return False
