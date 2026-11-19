from queue import Queue
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

class CrewEventListener(BaseEventListener):
    def __init__(self):
        super().__init__()

    def setup_listeners(self, event_bus):

        # Task events
        @event_bus.on(TaskStartedEvent)
        def on_task_started(source, event):
            event_queue.put({
                "type": "task_started",
                "agent": getattr(
                    getattr(event.task, "agent", None),
                    "role",
                    "Unknown agent",
                ),
            })

        @event_bus.on(TaskCompletedEvent)
        def on_task_completed(source, event):
            event_queue.put({
                "type": "task_completed",
                "agent": getattr(
                    getattr(event.task, "agent", None),
                    "role",
                    "Unknown agent",
                ),
            })

        @event_bus.on(TaskFailedEvent)
        def on_task_failed(source, event):
            event_queue.put({
                "type": "task_failed",
                "agent": getattr(
                    getattr(event.task, "agent", None),
                    "role",
                    "Unknown agent",
                ),
                "error": event.error,
            })

        # Standard tool events

        @event_bus.on(ToolUsageStartedEvent)
        def on_tool_started(source, event):
            event_queue.put({
                "type": "tool_started",
                "agent": event.agent_role or "Unknown agent",
                "tool": event.tool_name,
            })

        @event_bus.on(ToolUsageFinishedEvent)
        def on_tool_finished(source, event):
            event_queue.put({
                "type": "tool_finished",
                "agent": event.agent_role or "Unknown agent",
                "tool": event.tool_name,
                "failed": event.failure is not None,
            })

        @event_bus.on(ToolUsageErrorEvent)
        def on_tool_error(source, event):
            event_queue.put({
                "type": "tool_error",
                "agent": event.agent_role or "Unknown agent",
                "tool": event.tool_name,
                "error": str(event.error),
            })

        # MCP tool events
        @event_bus.on(MCPToolExecutionStartedEvent)
        def on_mcp_tool_started(source, event):
            event_queue.put({
                "type": "tool_started",
                "agent": event.agent_role or "Unknown agent",
                "tool": event.tool_name,
                "server": event.server_name,
            })

        @event_bus.on(MCPToolExecutionCompletedEvent)
        def on_mcp_tool_completed(source, event):
            event_queue.put({
                "type": "tool_finished",
                "agent": event.agent_role or "Unknown agent",
                "tool": event.tool_name,
                "server": event.server_name,
                "failed": False,
            })

        @event_bus.on(MCPToolExecutionFailedEvent)
        def on_mcp_tool_failed(source, event):
            event_queue.put({
                "type": "tool_error",
                "agent": event.agent_role or "Unknown agent",
                "tool": event.tool_name,
                "server": event.server_name,
                "error": event.error,
            })

listener = CrewEventListener()