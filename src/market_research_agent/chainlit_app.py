import asyncio
from queue import Empty
import chainlit as cl
from chainlit.input_widget import TextInput, Select
from market_research_agent.main import run
from market_research_agent.events import event_queue

# Only one crew run at a time
run_lock = asyncio.Lock()

@cl.on_chat_start     # Runs when a new Chainlit chat session starts
async def start():
    settings = await cl.ChatSettings([      # taking user inputs in UI Forms
        TextInput(
            id="business_idea",
            label="Business Idea",
            initial="",
            multiline=True,
        ),
        TextInput(
            id="business_problem",
            label="Business Problem",
            initial="",
            multiline=True,
        ),
        TextInput(
            id="business_objectives",
            label="Desired Business Objectives",
            initial="",
            multiline=True,
        ),
        TextInput(
            id="target_users",
            label="Target Users (Optional)",
            initial="",
        ),
        Select(
            id="industry",
            label="Industry",
            values=[
                "Not sure",
                "Software / SaaS",
                "Healthcare",
                "Education",
                "Finance",
                "Retail / E-commerce",
                "Manufacturing",
                "Other",
            ],
            initial_value="Not sure",
        ),
        TextInput(
            id="industry_details",
            label="Industry Details (Optional)",
            initial="",
        ),
        TextInput(
            id="target_geography",
            label="Target Geography (Optional)",
            initial="",
        ),
        TextInput(
            id="proposed_features",
            label="Proposed Features (Optional)",
            initial="",
            multiline=True,
        ),
        TextInput(
            id="existing_systems_constraints",
            label="Existing Systems / Constraints (Optional)",
            initial="",
            multiline=True,
        ),
    ]).send()

    cl.user_session.set("project_inputs", settings)

    await cl.Message(
        content=(
            "Fill in your project details in the settings panel "
            "and send **Generate BRD** to start the research."
        )
    ).send()

@cl.on_settings_update
async def update_settings(settings):
    cl.user_session.set("project_inputs", settings)

async def display_event(event, agent_steps, tool_steps):
    event_type = event["type"]

    # Agent task starts
    if event_type == "task_started":
        agent = event["agent"]
        step = cl.Step(
            name=agent,
            type="run",
            default_open=True,
        )

        step.input = "Task started."
        await step.send()
        agent_steps[agent] = step

    # Agent task completes
    elif event_type == "task_completed":
        step = agent_steps.get(event["agent"])

        if step:
            step.output = event["output"]
            await step.update()

    # Agent task fails
    elif event_type == "task_failed":
        step = agent_steps.get(event["agent"])

        if step:
            step.output = event["error"]
            step.is_error = True
            await step.update()

    # Tool starts
    elif event_type == "tool_started":

        agent = event["agent"]
        tool = event["tool"]
        parent = agent_steps.get(agent)
        step = cl.Step(
            name=tool,
            type="tool",
            parent_id=parent.id if parent else None,
            show_input=True,
        )

        step.input = event["input"]
        await step.send()
        tool_steps.setdefault((agent, tool), []).append(step)

    # Tool completes or fails
    elif event_type in ("tool_finished", "tool_error"):
        key = (event["agent"], event["tool"])
        steps = tool_steps.get(key, [])

        if steps:
            step = steps.pop(0)

            if not steps:
                tool_steps.pop(key)

            if event_type == "tool_error":
                step.output = event["error"]
                step.is_error = True
            else:
                step.output = event["output"]
                step.is_error = event["failed"]

            await step.update()

@cl.on_message
async def generate_brd(message: cl.Message):

    if message.content.strip().casefold() != "generate brd":
        await cl.Message(
            content="Send **Generate BRD** when your project details are ready."
        ).send()
        return

    inputs = cl.user_session.get("project_inputs", {})

    required_fields = [
        "business_idea",
        "business_problem",
        "business_objectives",
    ]

    if any(not (inputs.get(field) or "").strip() for field in required_fields):
        await cl.Message(
            content=(
                "Please complete the business idea, problem, "
                "and objectives first."
            )
        ).send()
        return

    async with run_lock:

        # Clear events from any previous execution
        while True:
            try:
                event_queue.get_nowait()
            except Empty:
                break

        agent_steps = {}
        tool_steps = {}

        await cl.Message(
            content="Starting the five-agent research workflow..."
        ).send()

        # Run CrewAI in a worker thread
        crew_task = asyncio.create_task(
            asyncio.to_thread(run, inputs)
        )

        # Read and display events while CrewAI is executing
        while not crew_task.done():

            try:
                event = event_queue.get_nowait()
            except Empty:
                await asyncio.sleep(0.1)
                continue

            await display_event(event, agent_steps, tool_steps)

        # Process remaining events after CrewAI finishes
        while True:

            try:
                event = event_queue.get_nowait()
            except Empty:
                break

            await display_event(event, agent_steps, tool_steps)

        try:
            result = await crew_task

        except Exception as error:
            await cl.Message(
                content=f"BRD generation failed: {error}"
            ).send()
            return

        await cl.Message(
            content=result.raw
        ).send()
