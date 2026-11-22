import os
import asyncio
from pathlib import Path
import httpx
from nicegui import ui
from market_research_agent.brd_docx_generator import create_brd_docx

from dotenv import load_dotenv
load_dotenv()

EXAMPLE_BRIEF = (
    "A mobile-first personal finance and micro-investing app called 'RupeeGrow' designed for salaried Gen-Z professionals in India. It automatically rounds up everyday UPI transactions to the nearest ₹10 or ₹50 and invests the spare change into diversified mutual funds and digital gold, solving the problem of low savings habits among young earners."
)

EXAMPLE_CONTEXT = (
    "Target Market: Indian urban salaried youth aged 21-27. Key Competitors: Jar, Gullak, Spare8. Regulatory environment: SEBI mutual fund distributor guidelines, RBI account aggregator framework."
)

async def execute_crew_on_amp(brief: str, context: str) -> str:
    # Sends the inputs to CrewAI AMP and polls until execution completes.
    api_url = os.getenv("AMP_API_URL", "").strip().rstrip("/")
    token = os.getenv("AMP_BEARER_TOKEN", "").strip()

    if not api_url or not token:
        raise ValueError("AMP credentials not set in environment.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Trigger Kickoff
        kickoff_res = await client.post(
            f"{api_url}/kickoff",
            headers=headers,
            json={"inputs": {"project_brief": brief, "additional_context": context}},
        )
        kickoff_res.raise_for_status()
        kickoff_id = kickoff_res.json().get("kickoff_id")

        if not kickoff_id:
            raise ValueError("No kickoff_id returned by AMP.")

        # 2. Poll Status every 4 seconds until done (approx 2-3 minutes)
        while True:
            await asyncio.sleep(4)
            status_res = await client.get(f"{api_url}/status/{kickoff_id}", headers=headers)
            status_res.raise_for_status()
            data = status_res.json()

            state = (data.get("state") or data.get("status") or "").lower()

            if state in {"completed", "success"}:
                result = data.get("result") or data.get("result_json")
                if isinstance(result, dict):
                    return result.get("output", "")
                return str(result or "")

            if state in {"failed", "error", "revoked"}:
                raise RuntimeError("The Crew execution failed on AMP.")

@ui.page("/")
def index():
    ui.page_title("Market Research & BRD Generator")

    with ui.column().classes("w-full max-w-4xl mx-auto p-8 gap-6"):

        # Header
        with ui.column().classes("gap-1"):
            ui.label("Market Research & BRD Generator").classes("text-3xl font-bold")
            ui.label("Multi-agent system for real-time market analysis and BRD generation.").classes("text-gray-500 text-sm")

        # Input Card
        with ui.card().classes("w-full p-6 gap-4"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label("Project Details").classes("text-lg font-semibold")

                def fill_sample():
                    brief_input.value = EXAMPLE_BRIEF
                    context_input.value = EXAMPLE_CONTEXT
                    ui.notify("Sample project idea loaded into fields.", type="info")

                ui.button("Try Example Idea", icon="lightbulb", on_click=fill_sample).props("flat dense color=primary")

            brief_input = ui.textarea(
                label="Business Idea & Problem Statement *",
                placeholder="Describe what your product solves, who the customers are, and the proposed solution...",
            ).classes("w-full").props("outlined rows=5")

            context_input = ui.textarea(
                label="Additional Context (Optional)",
                placeholder="Target geography, known competitors, pricing models, constraints...",
            ).classes("w-full").props("outlined rows=3")

            submit_btn = ui.button("Generate BRD", icon="auto_mode").classes("w-full py-3 text-base")

        # Feedback & Download Section
        spinner = ui.spinner(size="lg").classes("self-center")
        spinner.visible = False

        status_text = ui.label("").classes("text-center w-full text-gray-600 font-medium")
        download_box = ui.column().classes("w-full items-center")

        async def handle_generate():
            brief = (brief_input.value or "").strip()
            context = (context_input.value or "").strip()

            if not brief:
                ui.notify("Please enter a business idea before proceeding.", type="warning")
                return

            submit_btn.disable()
            spinner.visible = True
            download_box.clear()
            status_text.set_text("Agents are researching market, competitors, and customer data... (Takes 2-3 mins)")

            try:
                brd_markdown = await execute_crew_on_amp(brief, context)

                status_text.set_text("Generating your document...")
                docx_file = create_brd_docx(brd_markdown)

                status_text.set_text("Your Business Requirements Document is ready for download!")

                with download_box:
                    ui.button(
                        "Download Business Requirements Document (.docx)",
                        icon="download",
                        on_click=lambda: ui.download.file(str(docx_file)),
                    ).props("color=positive size=lg").classes("py-2 px-6")

                    # Preview
                    with ui.expansion("Preview Generated BRD Content", icon="visibility").classes("w-full border rounded-lg mt-3"):
                        ui.markdown(brd_markdown).classes("w-full p-4 bg-gray-50 dark:bg-gray-800 rounded")               

            except Exception as error:
                status_text.set_text("Generation interrupted.")
                ui.notify(f"Error: {error}", type="negative")

            finally:
                spinner.visible = False
                submit_btn.enable()

        submit_btn.on_click(handle_generate)

def main():
    ui.run(
        title="Market Research & BRD Generator",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        dark=False,
        reload=False,
    )

if __name__ == "__main__":
    main()