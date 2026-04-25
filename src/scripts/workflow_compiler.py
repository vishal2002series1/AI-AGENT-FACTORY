# src/scripts/workflow_compiler.py
import os
import json
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

def compile_domain_supervisor(workflow_id: str):
    base_dir = os.path.dirname(__file__)
    output_dir = os.path.abspath(os.path.join(base_dir, '../../src/workflows'))
    registry_path = os.path.abspath(os.path.join(base_dir, '../../data_local/agent_registry.json'))
    os.makedirs(output_dir, exist_ok=True)
    
    with open(registry_path, 'r') as f:
        agents = json.load(f)
    
    file_path = os.path.join(output_dir, f"{workflow_id.lower()}.py")
    agent_names = list(agents.keys())
    
    python_code = f"""# AUTO-COMPILED DOMAIN SUPERVISOR: {workflow_id}
import os
import sqlite3
import operator
from typing import Annotated, Sequence, TypedDict, Literal, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_aws import ChatBedrock
from pydantic import BaseModel, Field

from src.agents.config import registry_manager
from src.agents.factory import AgentFactory
from src.utils.prompt_manager import prompt_manager  # <-- Dynamic Prompts

class {workflow_id}State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_node: str
    instructions: str

# 🧠 Supervisor Routing Schema
class RouterOutput(BaseModel):
    next_node: Literal[{", ".join([f"'{n}'" for n in agent_names])}, 'FINISH'] = Field(
        ..., 
        description="The exact string name of the next agent to call, or 'FINISH'."
    )
    instructions: str = Field(..., description="Specific instructions for the next agent.")
    rejection_response: str = Field(
        default="", 
        description="ONLY USE THIS IF REJECTING A QUERY. If the user asks something completely out of scope, write a polite refusal here."
    )

def build_{workflow_id}_graph():
    factory = AgentFactory()
    builder = StateGraph({workflow_id}State)
    
    # 🏗️ Load Domain Workers
"""
    for name in agent_names:
        python_code += f"    builder.add_node('{name}', factory.build_node(registry_manager.agents.get('{name}')))\n"
    
    python_code += f"""
    # 👑 The Supervisor Node
    def supervisor(state: {workflow_id}State):
        model_id = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
        llm = ChatBedrock(model_id=model_id, region_name="us-east-1", temperature=0.0)
        
        # 🛑 Pull dynamic prompt
        system_prompt = prompt_manager.get_prompt("supervisor_system_prompt", agent_names="{agent_names}")
        
        messages_to_pass = list(state["messages"])
        if len(messages_to_pass) > 0 and messages_to_pass[-1].type != "human":
            nudge_text = prompt_manager.get_prompt("supervisor_nudge_prompt")
            messages_to_pass.append(HumanMessage(content=nudge_text))
        
        planner = llm.with_structured_output(RouterOutput)
        
        try:
             response = planner.invoke([SystemMessage(content=system_prompt)] + messages_to_pass)
             next_agent = response.next_node
             instructions = response.instructions
             rejection_text = response.rejection_response
        except Exception as e:
             print(f"      ⚠️ Supervisor parsing error: {{e}}. Defaulting to FINISH.")
             next_agent = "FINISH"
             instructions = "Error in routing."
             rejection_text = "I encountered an internal routing error."
             
        print(f"\\n👑 [SUPERVISOR] Routing to: {{next_agent}}")
        if next_agent != "FINISH":
             print(f"   ↳ Instructions: {{instructions}}")
             return {{"next_node": next_agent, "instructions": instructions}}
        else:
             if rejection_text:
                 return {{"next_node": next_agent, "instructions": instructions, "messages": [AIMessage(content=rejection_text)]}}
             return {{"next_node": next_agent, "instructions": instructions}}

    # 📝 The Final Synthesis Node (For Business Users)
    def synthesizer(state: {workflow_id}State):
        # If the last message is a rejection from the supervisor, just pass it through
        if len(state["messages"]) > 0 and state["messages"][-1].type == "ai":
             if "internal routing error" in state["messages"][-1].content or "outside the scope" in state["messages"][-1].content or "not able to" in state["messages"][-1].content:
                 return {{"messages": []}}

        model_id = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
        llm = ChatBedrock(model_id=model_id, region_name="us-east-1", temperature=0.2, max_tokens=8000)
        
        # 🛑 Pull dynamic prompt
        system_prompt = prompt_manager.get_prompt("synthesizer_system_prompt")
        
        messages_to_pass = list(state["messages"])
        if len(messages_to_pass) > 0 and messages_to_pass[-1].type != "human":
            nudge_text = prompt_manager.get_prompt("synthesizer_nudge_prompt")
            messages_to_pass.append(HumanMessage(content=nudge_text))
        
        print(f"\\n📝 [SYNTHESIZER] Formatting final response for associate...")
        response = llm.invoke([SystemMessage(content=system_prompt)] + messages_to_pass)
        return {{"messages": [response]}}

    builder.add_node("supervisor", supervisor)
    builder.add_node("synthesizer", synthesizer)

    # 🗺️ Logic: Always return to supervisor after a worker finishes
    for name in {agent_names}:
        builder.add_edge(name, "supervisor")

    # 🏁 Logic: Supervisor routes to Synthesizer on FINISH
    def should_continue(state: {workflow_id}State):
        if state["next_node"] == "FINISH":
            return "synthesizer"
        return state["next_node"]

    builder.add_conditional_edges("supervisor", should_continue)
    builder.add_edge("synthesizer", END)
    builder.add_edge(START, "supervisor")

    # 💾 Set up Persistent Database Memory
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data_local/sessions.db'))
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    memory.setup()  # Automatically creates the tables if they don't exist

    return builder.compile(checkpointer=memory)

if __name__ == "__main__":
    print("🎉 Successfully compiled Domain Supervisor graph with Synthesis.")
"""

    with open(file_path, 'w') as f:
        f.write(python_code)

if __name__ == "__main__":
    compile_domain_supervisor("WF_002")