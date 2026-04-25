# src/agents/fabricator.py
import os
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
from src.agents.tools import AEON_TOOLS

load_dotenv()

class AgentBlueprint(BaseModel):
    name: str = Field(..., description="Unique snake_case name for the agent (e.g., tax_analysis_agent).")
    routing_description: str = Field(..., description="Short 1-liner for the Supervisor to understand when to route here.")
    persona: str = Field(..., description="The full system prompt instructing the agent. Must include constraints to prevent hallucination.")
    authorized_tools: List[str] = Field(..., description="List of exact tool names this agent is allowed to use.")

class WorkflowEdge(BaseModel):
    source: str = Field(..., description="The name of the source node. Use 'START' for the beginning of the workflow.")
    target: str = Field(..., description="The name of the destination node. Use 'END' for the completion.")

class FabricatorOutput(BaseModel):
    new_agents: List[AgentBlueprint] = Field(
        ..., 
        description="MUST BE AN ARRAY. List of NEW agents to build. If existing agents can solve the task, YOU MUST PASS AN EMPTY ARRAY []."
    )
    edges: List[WorkflowEdge] = Field(
        ..., 
        description="MUST BE AN ARRAY. The Directed Acyclic Graph (DAG) routing edges."
    )

class AgentFabricator:
    def __init__(self):
        model_id = os.getenv("FABRICATOR_MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0")
        if not os.getenv("FABRICATOR_MODEL_ID"):
             model_id = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
             
        self.llm = ChatBedrock(
            model_id=model_id,
            region_name="us-east-1",
            temperature=0.2, 
            max_tokens=4096
        ).with_structured_output(FabricatorOutput)
        
        # Dynamically pulls [execute_sql, get_database_schema, compute_portfolio_concentration, search_transcripts, search_client_emails]
        self.available_tools = [tool.name for tool in AEON_TOOLS]

        self.system_prompt = f"""You are the Master Fabricator for the AEON Agent Factory.
Your job is to design highly specialized, granular AI agents AND their routing map to fulfill specific workflows.

AVAILABLE TOOLS IN THE REGISTRY:
{self.available_tools}

RULES FOR CREATION:
1. GRANULARITY: If the query requires multiple distinct capabilities (e.g., querying databases AND searching vectors), DO NOT build one agent to do both. You must return multiple Agent Blueprints, each representing a single, atomic skill.
2. TOOL BINDING: Assign a maximum of 1 or 2 highly related tools per agent. If an agent needs SQL, give it 'execute_sql' AND 'get_database_schema'.
3. ANTI-HALLUCINATION: The `persona` prompt MUST explicitly instruct the agent to cite its tool logs and NEVER guess financial data, tax rules, or client facts.
4. DAG ROUTING: You must provide the exact mapping edges in the `edges` output array. 
   - Workers run in parallel: (START -> worker_1), (START -> worker_2)
   - Workers funnel into synthesis: (worker_1 -> synthesis_agent), (worker_2 -> synthesis_agent)
   - Synthesis finishes: (synthesis_agent -> END)
5. GRACEFUL DEGRADATION: When writing the `persona` for ANY Synthesis Agent, you MUST explicitly inject this exact instruction: "You operate in a fault-tolerant environment. If one or more upstream tools or agents fail, DO NOT panic. You MUST aggressively extract and synthesize whatever valid data was successfully retrieved by the other agents to answer the user's prompt as completely as possible."
6. READ-ONLY DATABASE PROXY RULE (CRITICAL): You are operating on a strict, read-only enterprise database. You CANNOT assume the existence of perfect datetime columns (like `EstateDocumentLastUpdated` or `FinancialPlanLastUpdated`). When drafting SQL agents for date-based conditions, explicitly instruct them to use PROXY DATA (e.g., checking `SmartInsights.UpdatedAt`, `NextBestAction.Priority`, `Goals` JSON, or `TranscriptInsights` context) to infer staleness or missing documents.

You will receive a Test Query and optionally, Feedback from a Critic if a previous version of this agent hallucinated or failed.
"""

    def fabricate(self, test_query: str, critic_feedback: Optional[str] = None) -> FabricatorOutput:
        human_content = f"Please design an agent blueprint(s) AND a DAG topology to solve this query:\n{test_query}\n"
        
        if critic_feedback:
            human_content += f"\nCRITIC FEEDBACK FROM PREVIOUS RUN (You must fix these issues in the new persona/tools/DAG):\n{critic_feedback}"
            
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human_content)
        ]
        return self.llm.invoke(messages)