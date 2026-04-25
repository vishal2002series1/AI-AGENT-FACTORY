# src/agents/fabricator.py
import os
from pydantic import BaseModel, Field
from typing import List
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
from src.agents.tools import AEON_TOOLS
from src.utils.prompt_manager import prompt_manager # <-- NEW IMPORT

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

        # 🛑 Use the Prompt Manager instead of hardcoding
        self.system_prompt = prompt_manager.get_prompt("fabricator_system_prompt", available_tools=self.available_tools)

    def fabricate(self, workflow_name: str, description: str, data_sources: List[str]) -> DomainFabricatorOutput:
        human_content = f"Workflow: {workflow_name}\nDescription: {description}\nAvailable Tables: {data_sources}\n\nDesign the Domain Agents."
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human_content)
        ]
        return self.llm.invoke(messages)