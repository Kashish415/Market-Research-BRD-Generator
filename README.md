# Market Research Agent Crew

##### Input --> Startup idea

## 5 agents:  
1. Market research specialist agent 
2. Competitors study agent
3. Customer research agent
4. Product features designing agent
5. Business Analyst (takes reports from all 4 agents and compile one final report)

## Tasks:

1. Define agents.yaml (ROLE, GOAL, BACKSTORY) and tasks.yaml (DESC, EXPECTED OUTPUT, AGENT(optional))
2. Assemble both inside crew.py file. (config paths, agents, tasks, crew, tools)
3. Kickoff crew in main.py
4. check .env file for model name and api keys
5. Run in CLI: crewai run 
