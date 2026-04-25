# src/agents/fabricator.py
import os
from pydantic import BaseModel, Field
from typing import List
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
from src.agents.tools import AEON_TOOLS

load_dotenv()

class AgentBlueprint(BaseModel):
    name: str = Field(..., description="Unique snake_case name (e.g., compliance_domain_agent).")
    routing_description: str = Field(..., description="Clear description of WHAT this agent handles so the Supervisor knows when to route to it.")
    persona: str = Field(..., description="The system prompt. MUST include anti-hallucination rules and instructions to rely on exact tool outputs.")
    authorized_tools: List[str] = Field(..., description="Exact tool names this agent can use.")

class DomainFabricatorOutput(BaseModel):
    domain_agents: List[AgentBlueprint] = Field(..., description="List of domain-specific agents to handle the workflow.")

class DomainFabricator:
    def __init__(self):
        model_id = os.getenv("FABRICATOR_MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0")
        if not os.getenv("FABRICATOR_MODEL_ID"):
             model_id = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
             
        self.llm = ChatBedrock(
            model_id=model_id,
            region_name="us-east-1",
            temperature=0.2, 
            max_tokens=4096
        ).with_structured_output(DomainFabricatorOutput)
        
        self.available_tools = [tool.name for tool in AEON_TOOLS]

        self.system_prompt = f"""You are the Enterprise Domain Architect for the AEON Wealth Agent Factory.
Your job is to read a high-level Workflow Description and the Available Tables, and design a set of 3 to 6 highly capable, mutually exclusive Domain Agents to fulfill it.

AVAILABLE TOOLS IN THE REGISTRY:
{self.available_tools}

RULES FOR CREATION:
1. DOMAIN ISOLATION: Each agent must own a specific domain (e.g., Portfolio, Compliance, Interactions). Do NOT create overlap.
2. TOOL BINDING: Assign only the tools relevant to the domain. If they use SQL, give them 'execute_sql' AND 'get_database_schema'.
3. READ-ONLY PROXY RULE (CRITICAL): Explicitly instruct agents in their `persona` that they cannot assume perfect datetime columns exist for documents. They must use proxy data (like NextBestAction or TranscriptInsights) to infer status.
4. NO SYNTHESIS AGENT: Do NOT build a Synthesis Agent or a Supervisor. The system will handle orchestration automatically. Just build the worker agents.
"""

    def fabricate(self, workflow_name: str, description: str, data_sources: List[str]) -> DomainFabricatorOutput:
        human_content = f"Workflow: {workflow_name}\nDescription: {description}\nAvailable Tables: {data_sources}\n\nDesign the Domain Agents."
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human_content)
        ]
        return self.llm.invoke(messages)