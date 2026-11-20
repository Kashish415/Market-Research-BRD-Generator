from market_research_agent.crew import MarketResearchAgent
from market_research_agent.brd_docx_generator import create_brd_docx

def run(inputs):
    result = MarketResearchAgent().crew().kickoff(inputs=inputs)

    if not result.raw or not result.raw.strip():
        raise ValueError("The crew completed without returning BRD content.")

    create_brd_docx(result.raw)
    return result