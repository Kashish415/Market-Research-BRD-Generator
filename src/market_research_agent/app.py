import asyncio
from queue import Empty
from nicegui import run, ui
from market_research_agent.main import run as run_crew
from market_research_agent.events import event_queue
from market_research_agent.brd_docx_generator import create_brd_docx

# One generation at a time for this single-instance application.
generation_lock = asyncio.Lock()

@ui.page("/")
def index():
    ui.page_title("AI Business Analyst Assistant")

    with ui.column().classes("w-full max-w-5xl mx-auto p-6"):

        ui.label("AI Business Analyst Assistant").classes(
            "text-3xl font-bold"
        )

        ui.label(
            "Market research, competitor intelligence and BRD generation."
        ).classes("text-gray-500")

        with ui.card().classes("w-full"):

            ui.label("Project Overview").classes(
                "text-xl font-semibold"
            )

            project_brief = ui.textarea(
                label="Project Brief *",
                placeholder=(
                    "Describe your business idea, the problem it solves, "
                    "target users, objectives and proposed solution..."
                ),
            ).classes("w-full").props("rows=8")

            additional_context = ui.textarea(
                label="Additional Context (Optional)",
                placeholder=(
                    "Add any extra details such as industry, geography, "
                    "features, existing systems, constraints or preferences..."
                ),
            ).classes("w-full").props("rows=4")

        generate_button = ui.button(
            "Generate BRD",
            icon="description",
        ).classes("w-full")

        status = ui.label()

        activity_log = ui.log(max_lines=500).classes("w-full h-80")

        results = ui.column().classes("w-full")

    async def generate_brd():

        brief = (project_brief.value or "").strip()
        context = (additional_context.value or "").strip()

        if not brief:
            ui.notify(
                "Please enter your project brief.",
                type="warning",
            )
            return

        if generation_lock.locked():
            ui.notify(
                "A BRD generation is already running. Please try again later.",
                type="warning",
            )
            return

        async with generation_lock:

            generate_button.disable()

            status.set_text("Research in progress...")
            activity_log.push("Starting BRD generation...")
            results.clear()

            # Clear leftover events from any previous execution.
            while True:
                try:
                    event_queue.get_nowait()
                except Empty:
                    break

            inputs = {
                "project_brief": brief,
                "additional_context": context,
            }

            try:

                # Run CrewAI outside the NiceGUI event loop.
                crew_task = asyncio.create_task(
                    run.io_bound(run_crew, inputs)
                )

                # Display live CrewAI task and tool events.
                while not crew_task.done() or not event_queue.empty():

                    try:
                        event = event_queue.get_nowait()

                    except Empty:
                        await asyncio.sleep(0.1)
                        continue

                    message = event["type"].replace("_", " ").upper()
                    message += f" | {event.get('agent', '')}"

                    if event.get("tool"):
                        message += f" | {event['tool']}"

                    if event.get("failed"):
                        message += " | FAILED"

                    if event.get("error"):
                        message += f" | {event['error']}"

                    activity_log.push(message)

                result = await crew_task

                # Convert the final BRD content into an editable DOCX.
                docx_path = create_brd_docx(result.raw)

                status.set_text("BRD generation completed.")

                with results:

                    with ui.card().classes("w-full"):

                        ui.label(
                            "Your Business Requirements Document"
                        ).classes("text-xl font-semibold")

                        ui.button(
                            "Download Editable DOCX",
                            icon="download",
                            on_click=lambda: ui.download.file(
                                str(docx_path)
                            ),
                        )

                        with ui.expansion("Preview BRD"):
                            ui.markdown(result.raw)

                ui.notify(
                    "BRD generated successfully.",
                    type="positive",
                )

            except Exception as error:

                status.set_text("BRD generation failed.")

                ui.notify(
                    str(error),
                    type="negative",
                )

                activity_log.push(f"ERROR: {error}")

            finally:
                generate_button.enable()

    generate_button.on_click(generate_brd)

if __name__ == "__main__":

    ui.run(
        title="AI Business Analyst Assistant",
        port=8080,
        dark=True,
        reload=False,
    )
