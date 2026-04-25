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
    
    # Generate the Literal array for the LLM classifier
    intent_keys = list(dag.get("intents", {}).keys())
    intent_literal = ", ".join([f'"{i}"' for i in intent_keys]) + ', "UNKNOWN"'
    
    # Generate the routing map (Intent -> Start Nodes)
    routing_map_str = "{\n"
    internal_edges_str = ""
    
    # Extract ALL unique nodes from the edges
    all_nodes = set(dag.get("agents", []))
    for intent, edges in dag.get("intents", {}).items():
        start_nodes = []
        for edge in edges:
            src = edge["source"]
            tgt = edge["target"]
            
            if src.upper() != "START": all_nodes.add(src)
            if tgt.upper() != "END": all_nodes.add(tgt)
            
            if src.upper() == "START":
                start_nodes.append(tgt)
            else:
                tgt_fmt = "END" if tgt.upper() == "END" else f"'{tgt}'"
                internal_edges_str += f"    workflow.add_edge('{src}', {tgt_fmt})\n"
                
        routing_map_str += f'            "{intent}": {start_nodes},\n'
    routing_map_str += '        }'

    python_code = f"""# AUTO-COMPILED SEMANTIC WORKFLOW: {workflow_id}
import os
import operator
from typing import Annotated, Sequence, TypedDict, Literal
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_aws import ChatBedrock
from pydantic import BaseModel, Field

from src.agents.config import registry_manager, AgentConfig
from src.agents.factory import AgentFactory

class {workflow_id}State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: Annotated[list[str], operator.add]

# 🧠 Auto-Generated Semantic Classifier Schema
class IntentClassification(BaseModel):
    intent: Literal[{intent_literal}] = Field(
        ..., 
        description="Classify the user's query into one of these exact intents based on the conversation history."
    )

def build_{workflow_id}_graph():
    factory = AgentFactory()
    workflow = StateGraph({workflow_id}State)
    
"""
    # Load all required agents with a SAFEGUARD for missing agents
    for agent in all_nodes:
        python_code += f"""
    {agent}_cfg = registry_manager.agents.get('{agent}')
    if not {agent}_cfg:
        print(f"⚠️  WARNING: Agent '{agent}' was in DAG but not registry. Creating default fallback.")
        {agent}_cfg = AgentConfig(
            name='{agent}',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('{agent}', factory.build_node({agent}_cfg))
"""
    
    python_code += f"""
    # 🔀 Semantic Intent Router Node with Conversational Memory
    def semantic_router(state: {workflow_id}State) -> list[str]:
        model_id = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
        llm = ChatBedrock(model_id=model_id, region_name="us-east-1", temperature=0.0)
        classifier = llm.with_structured_output(IntentClassification)
        
        # Fetch the last 4 messages to give the router conversational context
        recent_messages = state["messages"][-4:]
        chat_history = "\\n".join([f"{{m.type}}: {{m.content}}" for m in recent_messages])
        
        try:
            classification = classifier.invoke([
                {{"role": "system", "content": "You are a Semantic Intent Router for a Wealth Management platform. Read the conversation history and classify the LATEST user intent. If it's a follow-up question, pick 'General conversational follow-up and ad-hoc queries'. If it matches nothing, select UNKNOWN."}},
                {{"role": "user", "content": f"Conversation History:\\n{{chat_history}}" }}
            ])
            intent = classification.intent
        except Exception as e:
            print(f"      ⚠️ Router Classification Failed: {{e}}")
            intent = "UNKNOWN"
            
        print(f"\\n   🔀 [MASTER ROUTER]: Classified Intent -> '{{intent}}'")
        
        routing_map = {routing_map_str}
        
        # If UNKNOWN, route to the Fallback Agent instead of END
        targets = routing_map.get(intent)
        if not targets or intent == "UNKNOWN":
            targets = routing_map.get("General conversational follow-up and ad-hoc queries", [END])
            
        print(f"   🚀 [MASTER ROUTER]: Firing parallel workers -> {{targets}}\\n")
        return targets

    # Connect START to our LLM Router
    possible_targets = {list(all_nodes)} + [END]
    workflow.add_conditional_edges(START, semantic_router, possible_targets)
    
    # Internal DAG Edges
{internal_edges_str}

    # Attach MemorySaver to persist state across chat turns
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
"""

    with open(file_path, 'w') as f:
        f.write(python_code)
    print(f"🎉 Successfully compiled semantic routing graph into: {file_path}")

if __name__ == "__main__":
    compile_workflow("WF_001")