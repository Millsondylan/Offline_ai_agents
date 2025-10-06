"""Tests for AgentController - Phase 2: Agent Integration."""

import asyncio
import time
from collections import deque
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

import pytest


class TestAgentController:
    """Test agent communication and control."""

    def test_agent_start_operation(self):
        """Test starting the agent."""
        from agent_control_panel.core.agent_controller import AgentController

        controller = AgentController()
        controller.start()

        assert controller.is_running() is True

    def test_agent_pause_operation(self):
        """Test pausing the agent."""
        from agent_control_panel.core.agent_controller import AgentController

        controller = AgentController()
        controller.start()
        controller.pause()

        assert controller.is_paused() is True

    def test_agent_stop_operation(self):
        """Test stopping the agent."""
        from agent_control_panel.core.agent_controller import AgentController

        controller = AgentController()
        controller.start()
        controller.stop()

        assert controller.is_running() is False

    def test_agent_status_polling(self):
        """Test getting current agent status."""
        from agent_control_panel.core.agent_controller import AgentController
        from agent_control_panel.core.models import AgentState

        controller = AgentController()
        status = controller.get_status()

        assert status is not None
        assert status.state == AgentState.IDLE
        assert status.current_cycle >= 0

    def test_thought_stream_subscription(self):
        """Test subscribing to agent thoughts."""
        from agent_control_panel.core.agent_controller import AgentController
        from agent_control_panel.core.models import Thought, ThoughtType

        controller = AgentController()
        thoughts_received = []

        def callback(thought):
            thoughts_received.append(thought)

        controller.subscribe_thoughts(callback)

        # Simulate thought
        test_thought = Thought(
            cycle=1,
            timestamp=datetime.now(),
            content="Test thought",
            thought_type=ThoughtType.REASONING,
        )
        controller._emit_thought(test_thought)

        time.sleep(0.1)  # Allow async processing
        assert len(thoughts_received) == 1
        assert thoughts_received[0].content == "Test thought"

    def test_log_stream_subscription(self):
        """Test subscribing to agent logs."""
        from agent_control_panel.core.agent_controller import AgentController
        from agent_control_panel.core.models import LogEntry, LogLevel

        controller = AgentController()
        logs_received = []

        def callback(log):
            logs_received.append(log)

        controller.subscribe_logs(callback)

        # Simulate log
        test_log = LogEntry(
            cycle=1,
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            message="Test log",
        )
        controller._emit_log(test_log)

        time.sleep(0.1)
        assert len(logs_received) == 1
        assert logs_received[0].message == "Test log"

    def test_agent_crash_detection(self):
        """Test detecting when agent process crashes."""
        from agent_control_panel.core.agent_controller import AgentController
        from agent_control_panel.core.models import AgentState

        controller = AgentController()
        controller.start()

        # Simulate crash
        controller._simulate_crash()

        status = controller.get_status()
        assert status.state == AgentState.ERROR
        assert status.last_error is not None

    def test_automatic_reconnection(self):
        """Test automatic reconnection after disconnect."""
        from agent_control_panel.core.agent_controller import AgentController

        controller = AgentController(auto_reconnect=True)
        controller.start()

        # Simulate disconnect
        controller._simulate_disconnect()

        # Should attempt reconnection
        time.sleep(0.5)
        assert controller.is_connected() or controller.is_reconnecting()

    def test_message_queue_thread_safety(self):
        """Test concurrent access to message queues."""
        from agent_control_panel.core.agent_controller import AgentController
        import threading

        controller = AgentController()
        errors = []

        def writer():
            try:
                for i in range(100):
                    controller._emit_thought(Mock(content=f"Thought {i}"))
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for _ in range(100):
                    controller.get_pending_thoughts()
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0  # No concurrent access errors

    @pytest.mark.asyncio
    async def test_async_event_handling(self):
        """Test async event handling."""
        from agent_control_panel.core.agent_controller import AgentController

        controller = AgentController()
        events_processed = []

        async def event_handler(event):
            events_processed.append(event)

        controller.register_async_handler(event_handler)

        # Emit events
        await controller.emit_event("test_event_1")
        await controller.emit_event("test_event_2")

        await asyncio.sleep(0.1)
        assert len(events_processed) == 2

    def test_graceful_shutdown(self):
        """Test controller shuts down cleanly."""
        from agent_control_panel.core.agent_controller import AgentController

        controller = AgentController()
        controller.start()

        # Subscribe to various streams
        controller.subscribe_thoughts(lambda t: None)
        controller.subscribe_logs(lambda l: None)

        # Shutdown
        controller.shutdown()

        # Should cleanup resources
        assert controller.is_running() is False
        assert controller._background_tasks_stopped()

    def test_status_updates_during_execution(self):
        """Test status updates as agent executes."""
        from agent_control_panel.core.agent_controller import AgentController

        controller = AgentController()
        controller.start()

        initial_status = controller.get_status()

        # Simulate execution
        controller._simulate_cycle_complete()

        updated_status = controller.get_status()
        assert updated_status.current_cycle > initial_status.current_cycle

    def test_error_recovery(self):
        """Test recovery from agent errors."""
        from agent_control_panel.core.agent_controller import AgentController
        from agent_control_panel.core.models import AgentState

        controller = AgentController()
        controller.start()

        # Cause error
        controller._simulate_error("Test error")

        status = controller.get_status()
        assert status.state == AgentState.ERROR

        # Recover
        controller.recover()

        status = controller.get_status()
        assert status.state != AgentState.ERROR

    def test_thought_queue_max_size(self):
        """Test thought queue doesn't exceed max size."""
        from agent_control_panel.core.agent_controller import AgentController

        controller = AgentController(max_thought_queue=100)

        # Add more than max
        for i in range(150):
            controller._emit_thought(Mock(content=f"Thought {i}"))

        thoughts = controller.get_pending_thoughts()
        assert len(thoughts) <= 100

    def test_log_queue_max_size(self):
        """Test log queue doesn't exceed max size."""
        from agent_control_panel.core.agent_controller import AgentController

        controller = AgentController(max_log_queue=100)

        # Add more than max
        for i in range(150):
            controller._emit_log(Mock(message=f"Log {i}"))

        logs = controller.get_pending_logs()
        assert len(logs) <= 100

    def test_connection_timeout(self):
        """Test connection attempt times out appropriately."""
        from agent_control_panel.core.agent_controller import AgentController

        controller = AgentController(connection_timeout=0.5)

        start_time = time.time()
        success = controller.connect_to_nonexistent_agent()
        elapsed = time.time() - start_time

        assert success is False
        assert elapsed < 1.0  # Should timeout quickly
