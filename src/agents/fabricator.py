# src/agents/fabricator.py
import os
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

class AgentBlueprint(BaseModel):
    name: str = Field(..., description="Unique snake_case name for the agent (e.g., tax_analysis_agent).")
    routing_description: str = Field(..., description="Short 1-liner for the Supervisor to understand when to route here.")
    persona: str = Field(..., description="The full system prompt instructing the agent. Must include constraints to prevent hallucination.")
    authorized_tools: List[str] = Field(..., description="List of exact tool names this agent is allowed to use.")

class FabricatorOutput(BaseModel):
    new_agents: List[AgentBlueprint] = Field(
        ..., 
        description="A list of 1 or more highly granular agents needed to fill the workflow gaps. Break complex workflows down into atomic agents."
    )

class AgentFabricator:
    def __init__(self):
        model_id = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
        self.llm = ChatBedrock(
            model_id=model_id,
            region_name="us-east-1",
            temperature=0.2, # Slight creativity to write excellent system prompts
            max_tokens=4096  # Increased to prevent truncation when generating multiple agents
        ).with_structured_output(FabricatorOutput)
        
        # The dynamic library of available tools in your factory
        self.available_tools = [
            "execute_sql", 
            "compute_portfolio_concentration", 
            "search_transcripts", 
            "search_market_news"
        ]

        self.system_prompt = f"""You are the Master Fabricator for the AEON Agent Factory.
Your job is to design highly specialized, granular AI agents to fulfill specific workflows.

AVAILABLE TOOLS IN THE REGISTRY:
{self.available_tools}

RULES FOR CREATION:
1. GRANULARITY: If the query requires multiple distinct capabilities (e.g., querying databases AND searching the web), DO NOT build one agent to do both. You must return multiple Agent Blueprints, each representing a single, atomic skill.
2. TOOL BINDING: Assign a maximum of 1 or 2 highly related tools per agent to ensure they remain specialized.
3. ANTI-HALLUCINATION: The `persona` prompt MUST explicitly instruct the agent to cite its tool logs and NEVER guess financial data, tax rules, or client facts.

You will receive a Test Query and optionally, Feedback from a Critic if a previous version of this agent hallucinated or failed.
"""

    def fabricate(self, test_query: str, critic_feedback: Optional[str] = None) -> FabricatorOutput:
        human_content = f"Please design an agent blueprint(s) to solve this query:\n{test_query}\n"
        
        if critic_feedback:
            human_content += f"\nCRITIC FEEDBACK FROM PREVIOUS RUN (You must fix these issues in the new persona/tools):\n{critic_feedback}"
            
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human_content)
        ]
        return self.llm.invoke(messages)