# Market Research Agent

This project accepts a business idea and generates market research, competitor analysis, customer insights, requirements, and an editable Business Requirements Document.

## Architecture

The project uses two deployments:

1. CrewAI AMP runs the existing Crew and stores execution history and traces.
2. A public NiceGUI application provides the website for entering a project brief and downloading the BRD.

The NiceGUI server calls AMP through its REST API. It does not start a second copy of the Crew.

## Crew workflow

The Crew has five agents:

1. Market Research Specialist
2. Competitive Intelligence Analyst
3. Customer Insights Researcher
4. Business Requirements Analyst
5. Senior Business Analyst and BRD Specialist

The first three research tasks run asynchronously. The requirements task runs synchronously after those reports. The final BRD task runs synchronously after the requirements task. The Crew process is sequential.

The first three agents use Exa MCP. OpenRouter supplies the configured LLM. Agent roles and task instructions remain in:

- `src/market_research_agent/config/agents.yaml`
- `src/market_research_agent/config/tasks.yaml`

## BRD download

When AMP finishes an execution, NiceGUI reads the completed result and creates a DOCX with `brd_docx_generator.py`. The generator uses `templates/BUSINESS REQUIREMENTS DOCUMENT.docx` and creates a unique file for each run.

The generated DOCX is downloaded by the browser. The file is not downloaded from an AMP container.

## Local setup

Requirements:

- Python 3.10 to 3.13
- `uv`

Install dependencies:

```bash
uv sync
```

Local environment variables:

- `AMP_API_URL`: Public AMP API base URL
- `AMP_BEARER_TOKEN`: Deployment bearer token
- `PORT`: Optional frontend port, default `8080`
- `HOST`: Optional frontend host, default `0.0.0.0`

Keep secrets in platform environment settings or set them in your terminal environment locally. Do not commit `.env` or API keys.

Start the frontend:

```bash
uv run market_research_ui
```

Open `http://localhost:8080`.

## CrewAI AMP deployment

1. Push the project to a GitHub repository.
2. In CrewAI AMP, choose **Deploy from Code**.
3. Select the repository and `feat/upgrade_brd` branch.
4. Configure `OPENROUTER_API_KEY` in the AMP deployment environment.
5. Deploy the Crew.
6. Copy the public AMP API URL and deployment bearer token.

The AMP deployment runs `src/market_research_agent/main.py` and `crew.py`. It does not run the NiceGUI application.

## Public NiceGUI deployment

Deploy this repository separately on a public Python hosting service that supports environment variables and WebSocket connections.

Set these values on the frontend service:

- `AMP_API_URL`
- `AMP_BEARER_TOKEN`
- `PORT`, if required by the hosting service

Use this start command:

```bash
uv run market_research_ui
```

The AMP bearer token remains on the NiceGUI server and is not sent to browser code or rendered in the page.

## API behaviour

NiceGUI sends a bearer-authenticated `POST /kickoff` request with:

```json
{
  "inputs": {
    "project_brief": "Business idea",
    "additional_context": "Optional context"
  }
}
```

It receives a `kickoff_id`, polls `GET /status/{kickoff_id}`, and stops when AMP reports `completed`, `error`, or `revoked`. Running executions are shown with `running` and available task progress. The frontend also accepts the newer `state` response format for compatibility. It does not show fabricated agent-level progress. The AMP `/progress` and task fields are used when they are available.

## Template and outputs

The DOCX template must remain at:

- `templates/BUSINESS REQUIREMENTS DOCUMENT.docx`

Generated files are stored under `outputs/` using a unique directory and filename for each run.

## Public submission limits

Public submissions are limited to two concurrent runs and a 60-second cooldown for each open page.