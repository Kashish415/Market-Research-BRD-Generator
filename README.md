# Market Research Agent

This project takes a business idea and produces market and customer research, a requirements specification, and a draft Business Requirements Document (BRD). It uses five CrewAI agents and can be deployed to CrewAI AMP.

## Agents and workflow

The Crew runs with a sequential process. The first three research tasks run asynchronously:

1. **Market Research Specialist** researches the market, trends, regulation, and opportunities.
2. **Competitive Intelligence Analyst** researches direct and indirect competitors, their offerings, and possible gaps.
3. **Customer Insights Researcher** researches customer segments, needs, and available evidence about buying behaviour.

The remaining tasks run synchronously:

4. **Business Requirements Analyst** uses the three research reports and the original brief to prepare a traceable requirements specification.
5. **Senior Business Analyst and BRD Specialist** uses the requirements specification to create the final BRD.

The requirements task depends on all three research tasks. The final BRD task depends on the requirements task. Agent roles and task instructions are in `src/market_research_agent/config/agents.yaml` and `src/market_research_agent/config/tasks.yaml`.

The first three agents use Exa through its hosted MCP endpoint. The Crew uses the OpenRouter-compatible LLM setup in `crew.py`.

## BRD document

After the final task returns its BRD, `main.py` passes the result to `brd_docx_generator.py`. The generator uses `templates/BUSINESS REQUIREMENTS DOCUMENT.docx` and saves an editable file under `outputs/`.

AMP's documented dashboard and execution API show text results, executions, traces, and metrics. They do not document a downloadable file artifact or a custom file-download route. The DOCX is generated in the deployment container, but users cannot download it directly through the documented AMP interface. Container files may not persist between deployments. The generator is kept, but DOCX download is not currently supported in AMP.

`templates/BRD_Template.docx` is also retained in the repository; the current generator uses `BUSINESS REQUIREMENTS DOCUMENT.docx`.

## Requirements

- Python 3.10 to 3.13
- `uv`
- An OpenRouter API key

Install the project dependencies from the repository root:

```bash
uv sync
```

## Deploy to CrewAI AMP

The project uses the classic Python/YAML Crew format supported by AMP. It has `type = "crew"` in `pyproject.toml` and includes `uv.lock`.

1. Push the project to a GitHub repository accessible to your AMP account. Include the `templates/` directory and `uv.lock`.
2. In CrewAI AMP, connect GitHub and select this repository and branch.
3. Add `OPENROUTER_API_KEY` in the AMP deployment's environment variables. Do not upload `.env`.
4. Deploy the project from the AMP dashboard.
5. Open the deployed Crew's **Run** tab and provide `project_brief` and `additional_context` inputs. Use an empty string for `additional_context` when there is no extra context.
6. Follow the run in **Executions** and inspect its **Traces** and metrics in the AMP dashboard.

The DOCX template is required at `templates/BUSINESS REQUIREMENTS DOCUMENT.docx` when the Crew runs. The current generator saves the file to `outputs/` in the container; AMP does not provide a documented direct download for it.

## References

- [Prepare for AMP deployment](https://docs-platform.crewai.com/platform/en/guides/prepare-for-deployment)
- [Deploy to AMP](https://docs-platform.crewai.com/platform/en/guides/deploy-to-amp)
- [Kick off a Crew in AMP](https://docs-platform.crewai.com/platform/en/guides/kickoff-crew)