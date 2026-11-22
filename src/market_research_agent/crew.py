import os
from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from dotenv import load_dotenv

load_dotenv()

llm = LLM(
    model="baidu/ernie-5.5-flash-preview:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    custom_openai=True,
    temperature=0.3,
)

exa_mcp = ["https://mcp.exa.ai/mcp"]

# 1. define the crew class
@CrewBase
class MarketResearchAgent():

    agents: list[BaseAgent]
    tasks: list[Task]

    # 2. provide path for config files
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # 3. create your agents
    @agent
    def market_research_specialist(self) -> Agent:
        return Agent(
            config = self.agents_config['market_research_specialist'],
            llm=llm,
            mcps=exa_mcp,
            max_iter=4
        )

    @agent
    def competitive_intelligence_analyst(self) -> Agent:
            return Agent(
                config = self.agents_config['competitive_intelligence_analyst'],
                llm=llm,
                mcps=exa_mcp,
                max_iter=4
            )

    @agent
    def customer_insights_researcher(self) -> Agent:
            return Agent(
                config = self.agents_config['customer_insights_researcher'],
                llm=llm,
                mcps=exa_mcp,
                max_iter=4
            )

    @agent
    def business_requirements_analyst(self) -> Agent:
            return Agent(
                config = self.agents_config['business_requirements_analyst'],
                llm= llm
            )

    @agent
    def business_analyst(self) -> Agent:
            return Agent(
                config = self.agents_config['business_analyst'],
                llm= llm
            )


    # 4. define your tasks (maintaining the order)
    @task
    def market_research_task(self) -> Task:
           return Task(
                  config=self.tasks_config["market_research_task"]
           )

    @task
    def competitive_intelligence_task(self) -> Task:
               return Task(
                      config=self.tasks_config["competitive_intelligence_task"]  
               )

    @task
    def customer_insights_task(self) -> Task:
               return Task(
                      config=self.tasks_config["customer_insights_task"]
               )

    @task
    def business_requirements_task(self) -> Task:
               return Task(
                      config=self.tasks_config["business_requirements_task"],
                      context=[self.market_research_task(),
                              self.competitive_intelligence_task(),
                              self.customer_insights_task()]
               )

    @task
    def business_analyst_task(self) -> Task:
            return Task(
                config=self.tasks_config["business_analyst_task"],
                context=[
                        self.business_requirements_task()
                ],
            )

    # 5. Form the Crew
    @crew
    def crew(self) -> Crew:
            return Crew(
                    agents= self.agents,
                    tasks= self.tasks,
                    process = Process.sequential,
                    tracing = True,
            )