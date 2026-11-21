import asyncio
import os
import time
from pathlib import Path
from uuid import uuid4

import httpx
from nicegui import ui

from market_research_agent.amp_api import (
    extract_brd_text,
    get_status,
    normalize_execution_status,
    progress_summary,
    start_execution,
)
from market_research_agent.brd_docx_generator import create_brd_docx


generation_semaphore = asyncio.Semaphore(2)


@ui.page("/")
def index():
    ui.page_title("AI Business Analyst Assistant")

    with ui.column().classes("w-full max-w-5xl mx-auto p-6"):
        ui.label("AI Business Analyst Assistant").classes("text-3xl font-bold")
        ui.label("Market research, competitor intelligence and BRD generation.").classes("text-gray-500")

        with ui.card().classes("w-full"):
            ui.label("Project Overview").classes("text-xl font-semibold")

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

        generate_button = ui.button("Generate BRD", icon="description").classes("w-full")
        status = ui.label()
        activity_log = ui.log(max_lines=500).classes("w-full h-80")
        results = ui.column().classes("w-full")

    generation_lock = asyncio.Lock()
    last_submission = 0.0

    async def generate_brd():
        nonlocal last_submission

        current_time = time.monotonic()
        if current_time - last_submission < 60:
            remaining = 60 - (current_time - last_submission)
            ui.notify(f"Please wait {remaining:.0f} seconds before submitting again.", type="warning")
            return

        brief = (project_brief.value or "").strip()
        context = (additional_context.value or "").strip()

        if not brief:
            ui.notify("Please enter your project brief.", type="warning")
            return

        if len(brief) > 20_000:
            ui.notify("Please keep the project brief under 20,000 characters.", type="warning")
            return

        if len(context) > 10_000:
            ui.notify("Please keep additional context under 10,000 characters.", type="warning")
            return

        if generation_lock.locked():
            ui.notify("A BRD generation is already running.", type="warning")
            return

        async with generation_lock:
            last_submission = time.monotonic()
            generate_button.disable()
            results.clear()
            activity_log.clear()
            status.set_text("Starting AMP execution...")

            api_url = os.getenv("AMP_API_URL", "").strip()
            bearer_token = os.getenv("AMP_BEARER_TOKEN", "").strip()

            if not api_url or not bearer_token:
                status.set_text("AMP configuration is missing.")
                activity_log.push("Configure AMP_API_URL and AMP_BEARER_TOKEN on the frontend server.")
                ui.notify("AMP configuration is missing.", type="negative")
                generate_button.enable()
                return

            try:
                async with generation_semaphore:
                    async with httpx.AsyncClient(
                        timeout=httpx.Timeout(30.0),
                        follow_redirects=True,
                    ) as client:
                        kickoff_id = await start_execution(
                            client,
                            api_url,
                            bearer_token,
                            {
                                "project_brief": brief,
                                "additional_context": context,
                            },
                        )

                        activity_log.push(f"AMP execution started | {kickoff_id}")
                        status.set_text("AMP execution running...")

                        deadline = time.monotonic() + 900
                        last_activity = ""

                        while True:
                            result_status = await get_status(
                                client,
                                api_url,
                                bearer_token,
                                kickoff_id,
                            )

                            state = normalize_execution_status(result_status)

                            if state == "completed":
                                break

                            if state == "failed":
                                error = result_status.get("error") or result_status.get("status")
                                if error:
                                    raise RuntimeError(f"AMP execution failed: {error}")
                                raise RuntimeError("AMP execution failed.")

                            if state == "paused":
                                raise RuntimeError("AMP execution is paused and is waiting for human input.")

                            if state != "running":
                                raise RuntimeError("AMP returned an unknown execution state.")

                            progress = progress_summary(result_status)
                            activity = "RUNNING"
                            if progress:
                                activity += f" | {progress}"

                            if activity != last_activity:
                                status.set_text(f"AMP execution | {activity}")
                                activity_log.push(activity)
                                last_activity = activity

                            if time.monotonic() >= deadline:
                                raise TimeoutError("AMP execution timed out.")

                            await asyncio.sleep(5)

                brd_text = extract_brd_text(result_status)

                output_dir = Path("outputs") / uuid4().hex
                docx_path = create_brd_docx(brd_text, output_dir=output_dir)

                status.set_text("BRD generation completed.")
                activity_log.push("BRD content received.")
                activity_log.push("Editable DOCX generated.")

                with results:
                    with ui.card().classes("w-full"):
                        ui.label("Your Business Requirements Document").classes("text-xl font-semibold")
                        ui.button(
                            "Download Editable DOCX",
                            icon="download",
                            on_click=lambda: ui.download.file(
                                str(docx_path),
                                filename=docx_path.name,
                                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            ),
                        )
                        with ui.expansion("Final BRD Preview"):
                            ui.markdown(brd_text)

                ui.notify("BRD generated successfully.", type="positive")

            except TimeoutError:
                status.set_text("AMP execution timed out.")
                activity_log.push("Execution timed out. Check the AMP Executions and Traces pages.")
                ui.notify("The AMP execution timed out.", type="negative")

            except httpx.HTTPError:
                status.set_text("Could not reach CrewAI AMP.")
                activity_log.push("AMP request failed. Check the frontend server network and AMP credentials.")
                ui.notify("Could not reach CrewAI AMP.", type="negative")

            except Exception as error:
                status.set_text("BRD generation failed.")
                activity_log.push(f"ERROR: {error}")
                ui.notify(str(error), type="negative")

            finally:
                generate_button.enable()

    generate_button.on_click(generate_brd)


def main():
    ui.run(
        title="AI Business Analyst Assistant",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        dark=True,
        reload=False,
    )


if __name__ == "__main__":
    main()
