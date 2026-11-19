from queue import Queue
from time import perf_counter
from threading import Lock
from crewai.events import (
    BaseEventListener,
    TaskStartedEvent,
    TaskCompletedEvent,
    TaskFailedEvent,
    ToolUsageStartedEvent,
    ToolUsageFinishedEvent,
    ToolUsageErrorEvent,
    MCPToolExecutionStartedEvent,
    MCPToolExecutionCompletedEvent,
    MCPToolExecutionFailedEvent,
)

event_queue = Queue()
task_start_times = {}
task_lock = Lock()

class CrewEventListener(BaseEventListener):
    def setup_listeners(self, event_bus):

        @event_bus.on(TaskStartedEvent)
        def on_task_started(source, event):
            with task_lock:
                task_start_times[id(event.task)] = perf_counter()

            event_queue.put({
                "type": "task_started",
                "agent": event.task.agent.role,
            })

        @event_bus.on(TaskCompletedEvent)
        def on_task_completed(source, event):
            with task_lock:
                started_at = task_start_times.pop(id(event.task), None)

            duration = (
                round(perf_counter() - started_at, 2)
                if started_at is not None
                else None
            )

            event_queue.put({
                "type": "task_completed",
                "agent": event.task.agent.role,
                "duration_seconds": duration,
            })

        @event_bus.on(TaskFailedEvent)
        def on_task_failed(source, event):
            with task_lock:
                started_at = task_start_times.pop(id(event.task), None)

            duration = (
                round(perf_counter() - started_at, 2)
                if started_at is not None
                else None
            )

            event_queue.put({
                "type": "task_failed",
                "agent": event.task.agent.role,
                "duration_seconds": duration,
                "error": str(event.error),
            })

        @event_bus.on(ToolUsageStartedEvent)
        def on_tool_started(source, event):
            event_queue.put({
                "type": "tool_started",
                "agent": event.agent_role or "Unknown",
                "tool": event.tool_name,
            })

        @event_bus.on(ToolUsageFinishedEvent)
        def on_tool_finished(source, event):
            event_queue.put({
                "type": "tool_finished",
                "agent": event.agent_role or "Unknown",
                "tool": event.tool_name,
                "failed": event.failure is not None,
            })

        @event_bus.on(ToolUsageErrorEvent)
        def on_tool_error(source, event):
            event_queue.put({
                "type": "tool_error",
                "agent": event.agent_role or "Unknown",
                "tool": event.tool_name,
                "error": str(event.error),
            })

        @event_bus.on(MCPToolExecutionStartedEvent)
        def on_mcp_tool_started(source, event):
            event_queue.put({
                "type": "tool_started",
                "agent": event.agent_role or "Unknown",
                "tool": event.tool_name,
                "server": event.server_name,
            })

        @event_bus.on(MCPToolExecutionCompletedEvent)
        def on_mcp_tool_completed(source, event):
            event_queue.put({
                "type": "tool_finished",
                "agent": event.agent_role or "Unknown",
                "tool": event.tool_name,
                "server": event.server_name,
            })

        @event_bus.on(MCPToolExecutionFailedEvent)
        def on_mcp_tool_failed(source, event):
            event_queue.put({
                "type": "tool_error",
                "agent": event.agent_role or "Unknown",
                "tool": event.tool_name,
                "server": event.server_name,
                "error": str(event.error),
            })

listener = CrewEventListener()