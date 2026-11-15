from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

# toolS for web search capability and scraping!
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, SeleniumScrapingTool 

from dotenv import load_dotenv
load_dotenv()

# create the tools for the agents
web_search_tool = SerperDevTool()
web_scraping_tool = ScrapeWebsiteTool()
selenium_scraping_tool = SeleniumScrapingTool()
# expose all tools as toolkit in a list of tools 
toolkit = [web_search_tool, web_scraping_tool, selenium_scraping_tool]   # pass as parameter in agents below

# 1. define the crew class
@CrewBase
class MarketResearchAgent():

    agents: List[BaseAgent]
    tasks: List[Task]

    # 2. provide path for config files
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # 3. create your agents
    @agent
    def market_research_specialist(self) -> Agent:
        return Agent(
            config = self.agents_config['market_research_specialist'],
            tools= toolkit
        )

    @agent
    def competitive_intelligence_analyst(self) -> Agent:
            return Agent(
                config = self.agents_config['competitive_intelligence_analyst'],
                tools= toolkit
            )


    @agent
    def customer_insights_researcher(self) -> Agent:
            return Agent(
                config = self.agents_config['customer_insights_researcher'],
                tools= toolkit
            )


    @agent
    def product_strategy_advisor(self) -> Agent:
            return Agent(
                config = self.agents_config['product_strategy_advisor'],
                tools= toolkit
            )


    @agent
    def business_analyst(self) -> Agent:
            return Agent(
                config = self.agents_config['business_analyst'],
                tools= toolkit
            )

    # 4. define your tasks (maintaining the order)
    ### EACH TASK NEEDS THE CONTEXT/OUTPUT OF ITS PRECEDING TASKS!
    @task
    def market_research_task(self) -> Task:
           return Task(
                  config=self.tasks_config["market_research_task"],
                  tools= toolkit
           )

    @task
    def competitive_intelligence_task(self) -> Task:
               return Task(
                      config=self.tasks_config["competitive_intelligence_task"],
                      context=[self.market_research_task()]    # pass in a list the whole context
               )

    @task
    def customer_insights_task(self) -> Task:
               return Task(
                      config=self.tasks_config["customer_insights_task"],
                      context= [self.market_research_task(),
                                self.competitive_intelligence_task()]
               )

    @task
    def product_strategy_task(self) -> Task:
               return Task(
                      config=self.tasks_config["product_strategy_task"],
                      context=[self.market_research_task(),
                              self.competitive_intelligence_task(),
                              self.customer_insights_task()]
               )

    @task
    def business_analyst_task(self) -> Task:
               return Task(
                      config=self.tasks_config["business_analyst_task"],
                      context= [self.market_research_task(),
                                self.competitive_intelligence_task(),
                                self.customer_insights_task(),
                                self.product_strategy_task()]
               )

    # 5. Form your Crew

    @crew
    def crew(self) -> Crew:
            return Crew(
                    agents= self.agents,
                    tasks= self.tasks,
                    process = Process.sequential
                    
            )
    

