import asyncio
from queue import Empty
from time import perf_counter
from nicegui import run, ui
from market_research_agent.main import run as run_crew
from market_research_agent.events import event_queue
from market_research_agent.brd_docx_generator import create_brd_docx

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
                    "Add extra details such as industry, geography, "
                    "features, constraints or preferences..."
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
            ui.notify("Please enter your project brief.", type="warning")
            return

        if generation_lock.locked():
            ui.notify("A generation is already running.", type="warning")
            return

        async with generation_lock:

            generate_button.disable()
            results.clear()
            activity_log.clear()

            while True:
                try:
                    event_queue.get_nowait()
                except Empty:
                    break

            inputs = {
                "project_brief": brief,
                "additional_context": context,
            }

            streamed_brd = ""
            generation_started = perf_counter()
            last_preview_update = 0

            status.set_text("Research and BRD generation in progress...")

            with results:
                with ui.card().classes("w-full"):
                    ui.label("Live BRD Preview").classes(
                        "text-xl font-semibold"
                    )
                    brd_preview = ui.markdown("")

            try:
                crew_task = asyncio.create_task(
                    run.io_bound(run_crew, inputs)
                )

                while not crew_task.done() or not event_queue.empty():

                    try:
                        event = event_queue.get_nowait()

                    except Empty:
                        await asyncio.sleep(0.1)
                        continue

                    if event["type"] == "brd_stream_chunk":
                        streamed_brd += event["content"]

                        if perf_counter() - last_preview_update >= 0.2:
                            brd_preview.set_content(streamed_brd)
                            last_preview_update = perf_counter()

                        continue

                    message = event["type"].replace("_", " ").upper()
                    message += f" | {event.get('agent', '')}"

                    if event.get("tool"):
                        message += f" | {event['tool']}"

                    if event.get("duration_seconds") is not None:
                        message += (
                            f" | {event['duration_seconds']:.1f}s"
                        )

                    if event.get("error"):
                        message += f" | {event['error']}"

                    activity_log.push(message)

                result = await crew_task

                brd_preview.set_content(result.raw)

                docx_path = create_brd_docx(result.raw)

                total_time = perf_counter() - generation_started

                activity_log.push(
                    f"TOTAL GENERATION TIME | {total_time:.1f}s"
                )

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

                        with ui.expansion("Final BRD Preview"):
                            ui.markdown(result.raw)

                ui.notify(
                    "BRD generated successfully.",
                    type="positive",
                )

            except Exception as error:
                status.set_text("BRD generation failed.")
                activity_log.push(f"ERROR: {error}")
                ui.notify(str(error), type="negative")

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