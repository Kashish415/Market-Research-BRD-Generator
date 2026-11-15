from market_research_agent.crew import MarketResearchAgent

def run():
    inputs = {
        'product_idea': "An AI-powered personal finance assistant that tracks expenses and provides smart budgeting recommendations."
    }
    # product_idea came from placeholder in tasks.yaml file

    result = MarketResearchAgent().crew().kickoff(inputs=inputs)
    print(result)


