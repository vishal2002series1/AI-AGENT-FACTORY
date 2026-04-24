# src/scripts/workflow_compiler.py
import os
import json

def compile_workflow(workflow_id: str):
    base_dir = os.path.dirname(__file__)
    dag_path = os.path.abspath(os.path.join(base_dir, f'../../workflows/{workflow_id}_dag.json'))
    output_dir = os.path.abspath(os.path.join(base_dir, '../../src/workflows'))
    os.makedirs(output_dir, exist_ok=True)
    
    with open(dag_path, 'r') as f:
        dag = json.load(f)
        
    file_path = os.path.join(output_dir, f"{workflow_id.lower()}.py")
    
    python_code = f"""# AUTO-COMPILED WORKFLOW: {workflow_id}
import operator
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from src.agents.config import registry_manager
from src.agents.factory import AgentFactory

class {workflow_id}State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: Annotated[list[str], operator.add]

def build_{workflow_id}_graph():
    factory = AgentFactory()
    workflow = StateGraph({workflow_id}State)
    
"""
    # 🛑 BULLETPROOF FIX: Extract ALL unique nodes from the edges to guarantee no missing nodes
    all_nodes = set(dag.get("agents", []))
    for edge in dag.get("edges", []):
        if edge["source"].upper() != "START":
            all_nodes.add(edge["source"])
        if edge["target"].upper() != "END":
            all_nodes.add(edge["target"])

    # Load all the required agents
    for agent in all_nodes:
        python_code += f"    {agent}_cfg = registry_manager.agents.get('{agent}')\n"
        python_code += f"    workflow.add_node('{agent}', factory.build_node({agent}_cfg))\n"
    
    python_code += "\n    # Declarative Routing\n"
    # Build the exact mathematical edges designed by the Fabricator
    for edge in dag["edges"]:
        src = "START" if edge["source"].upper() == "START" else f"'{edge['source']}'"
        tgt = "END" if edge["target"].upper() == "END" else f"'{edge['target']}'"
        python_code += f"    workflow.add_edge({src}, {tgt})\n"

    python_code += f"\n    return workflow.compile()\n"

    with open(file_path, 'w') as f:
        f.write(python_code)
    print(f"🎉 Successfully compiled declarative graph into: {file_path}")

if __name__ == "__main__":
    compile_workflow("WF_001")