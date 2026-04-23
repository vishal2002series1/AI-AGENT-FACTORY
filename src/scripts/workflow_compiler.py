# src/scripts/workflow_compiler.py
import os
import json

def compile_workflow(workflow_id: str, workflow_name: str, agent_names: list):
    """
    Generates a hardcoded, static Python file (Sub-Graph) for a specific workflow.
    """
    base_dir = os.path.dirname(__file__)
    output_dir = os.path.abspath(os.path.join(base_dir, '../../src/workflows'))
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, f"{workflow_id.lower()}.py")
    
    # The template for our compiled Python workflow
    python_code = f"""# AUTO-COMPILED WORKFLOW: {workflow_name}
# This is a statically governed Sub-Graph. Do not edit routing logic manually unless authorized.

import operator
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from src.agents.config import registry_manager
from src.agents.factory import AgentFactory

# 1. Define Sub-Graph State
class {workflow_id}State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: Annotated[list[str], operator.add]

# 2. Build the Static Graph
def build_{workflow_id}_graph():
    factory = AgentFactory()
    workflow = StateGraph({workflow_id}State)
    
    # 3. Load Authorized Agents
"""
    
    # Add nodes for each agent
    for agent in agent_names:
        python_code += f"    {agent}_config = registry_manager.agents.get('{agent}')\n"
        python_code += f"    workflow.add_node('{agent}', factory.build_node({agent}_config))\n"
    
    # ... inside compile_workflow ...
    
    python_code += "\n    # 4. Hardcode the Routing Edges (Parallel Execution -> Synthesis -> End)\n"
    
    # FIX: Broaden the search for the synthesis agent
    synthesis_keywords = ["synthesis", "reporter", "summarizer", "writer"]
    synthesis_agent = [a for a in agent_names if any(kw in a.lower() for kw in synthesis_keywords)]
    workers = [a for a in agent_names if a not in synthesis_agent]
    
    for worker in workers:
        python_code += f"    workflow.add_edge(START, '{worker}')\n"
    
    if synthesis_agent:
        synth = synthesis_agent[0]
        # Workers funnel into the synthesis agent
        for worker in workers:
            python_code += f"    workflow.add_edge('{worker}', '{synth}')\n"
        # Synthesis agent goes to END
        python_code += f"    workflow.add_edge('{synth}', END)\n"
    else:
        for worker in workers:
            python_code += f"    workflow.add_edge('{worker}', END)\n"

    # ... rest of the script

    python_code += f"""
    return workflow.compile()

# To use this as a Sub-Graph or test it independently:
if __name__ == "__main__":
    app = build_{workflow_id}_graph()
    print("✅ {workflow_id} Compiled Graph Loaded Successfully.")
"""

    with open(file_path, 'w') as f:
        f.write(python_code)
        
    print(f"🎉 Successfully compiled {workflow_id} into: {file_path}")

if __name__ == "__main__":
    # We will compile the 3 agents we just generated in the Sandbox into WF_001
    compiled_agents = [
        "life_event_detector_agent",
        "financial_plan_review_checker_agent",
        "at_risk_client_gap_reporter_agent" # This acts as our synthesis agent for this workflow
    ]
    
    compile_workflow("WF_001", "Client Review and Prep", compiled_agents)