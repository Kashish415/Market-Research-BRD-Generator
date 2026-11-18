# This file helps in listening to CrewAI's task and tool execution events and puts them into a queue, which Chainlit will read to display each agent's live execution.

from queue import Queue

from crewai.events import (
    BaseEventListener,
    TaskStartedEvent,
    TaskCompletedEvent,
    TaskFailedEvent,
    ToolUsageStartedEvent,
    ToolUsageFinishedEvent,
    ToolUsageErrorEvent,
)

event_queue = Queue()

class CrewEventListener(BaseEventListener):

    def setup_listeners(self, event_bus):

        # Task events
        @event_bus.on(TaskStartedEvent)
        def on_task_started(source, event):
            event_queue.put({          # Every time an event occurs, we put its details into this event_queue.
                "type": "task_started",
                "agent": event.task.agent.role,
            })

        @event_bus.on(TaskCompletedEvent)
        def on_task_completed(source, event):
            event_queue.put({
                "type": "task_completed",
                "agent": event.task.agent.role,
                "output": event.output.raw,
            })

        @event_bus.on(TaskFailedEvent)
        def on_task_failed(source, event):
            event_queue.put({
                "type": "task_failed",
                "agent": event.task.agent.role,
                "error": event.error,
            })

        # Tool events
        @event_bus.on(ToolUsageStartedEvent)
        def on_tool_started(source, event):
            event_queue.put({
                "type": "tool_started",
                "agent": event.agent_role,
                "tool": event.tool_name,
                "input": event.tool_args,
            })

        @event_bus.on(ToolUsageFinishedEvent)
        def on_tool_finished(source, event):
            event_queue.put({
                "type": "tool_finished",
                "agent": event.agent_role,
                "tool": event.tool_name,
                "output": str(event.output),
                "failed": event.failure is not None,
            })

        @event_bus.on(ToolUsageErrorEvent)
        def on_tool_error(source, event):
            event_queue.put({
                "type": "tool_error",
                "agent": event.agent_role,
                "tool": event.tool_name,
                "error": str(event.error),
            })

listener = CrewEventListener()