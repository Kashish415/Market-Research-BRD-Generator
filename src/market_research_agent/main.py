from market_research_agent.crew import MarketResearchAgent

def run(inputs):
    return MarketResearchAgent().crew().kickoff(inputs=inputs)