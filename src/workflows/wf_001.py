# AUTO-COMPILED DOMAIN SUPERVISOR: WF_001
import os
import operator
from typing import Annotated, Sequence, TypedDict, Literal, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_aws import ChatBedrock
from pydantic import BaseModel, Field

from src.agents.config import registry_manager
from src.agents.factory import AgentFactory

class WF_001State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_node: str
    instructions: str

# 🧠 Supervisor Routing Schema
class RouterOutput(BaseModel):
    next_node: Literal['client_profile_domain_agent', 'portfolio_domain_agent', 'interactions_domain_agent', 'compliance_documents_domain_agent', 'email_communications_domain_agent', 'FINISH'] = Field(
        ..., 
        description="The exact string name of the next agent to call, or 'FINISH'."
    )
    instructions: str = Field(..., description="Specific instructions for the next agent.")
    rejection_response: str = Field(
        default="", 
        description="ONLY USE THIS IF REJECTING A QUERY. If the user asks something completely out of scope (like writing code or restaurant recommendations), write a polite refusal here. Otherwise, leave blank."
    )

def build_WF_001_graph():
    factory = AgentFactory()
    builder = StateGraph(WF_001State)
    
    # 🏗️ Load Domain Workers
    builder.add_node('client_profile_domain_agent', factory.build_node(registry_manager.agents.get('client_profile_domain_agent')))
    builder.add_node('portfolio_domain_agent', factory.build_node(registry_manager.agents.get('portfolio_domain_agent')))
    builder.add_node('interactions_domain_agent', factory.build_node(registry_manager.agents.get('interactions_domain_agent')))
    builder.add_node('compliance_documents_domain_agent', factory.build_node(registry_manager.agents.get('compliance_documents_domain_agent')))
    builder.add_node('email_communications_domain_agent', factory.build_node(registry_manager.agents.get('email_communications_domain_agent')))

    # 👑 The Supervisor Node
    def supervisor(state: WF_001State):
        model_id = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
        llm = ChatBedrock(model_id=model_id, region_name="us-east-1", temperature=0.0)
        
        system_prompt = (
            "You are the invisible Orchestrator for a Wealth Management workflow. "
            "Your job is to route to the correct data-gathering agents. "
            "Available Agents: ['client_profile_domain_agent', 'portfolio_domain_agent', 'interactions_domain_agent', 'compliance_documents_domain_agent', 'email_communications_domain_agent']. "
            "Strategy: Call agents one by one to gather required SQL/Tool data. "
            "When all necessary raw data is in the chat history, select FINISH. Do NOT summarize the data yourself."
        )
        
        messages_to_pass = list(state["messages"])
        if len(messages_to_pass) > 0 and messages_to_pass[-1].type != "human":
            nudge = HumanMessage(content="Based on the data gathered so far, what agent should I call next? Or should I FINISH?")
            messages_to_pass.append(nudge)
        
        planner = llm.with_structured_output(RouterOutput)
        
        try:
             response = planner.invoke([SystemMessage(content=system_prompt)] + messages_to_pass)
             next_agent = response.next_node
             instructions = response.instructions
             rejection_text = response.rejection_response
        except Exception as e:
             print(f"      ⚠️ Supervisor parsing error: {e}. Defaulting to FINISH.")
             next_agent = "FINISH"
             instructions = "Error in routing."
             rejection_text = "I encountered an internal routing error."
             
        print(f"\n👑 [SUPERVISOR] Routing to: {next_agent}")
        if next_agent != "FINISH":
             print(f"   ↳ Instructions: {instructions}")
             return {"next_node": next_agent, "instructions": instructions}
        else:
             if rejection_text:
                 return {"next_node": next_agent, "instructions": instructions, "messages": [AIMessage(content=rejection_text)]}
             return {"next_node": next_agent, "instructions": instructions}

    # 📝 The Final Synthesis Node (For Business Users)
    # 📝 The Final Synthesis Node (For Business Users)
    def synthesizer(state: WF_001State):
        # If the last message is a rejection from the supervisor, just pass it through
        if len(state["messages"]) > 0 and state["messages"][-1].type == "ai":
             if "internal routing error" in state["messages"][-1].content or "outside the scope" in state["messages"][-1].content or "not able to" in state["messages"][-1].content:
                 return {"messages": []}

        model_id = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
        llm = ChatBedrock(model_id=model_id, region_name="us-east-1", temperature=0.2)
        
        system_prompt = (
            "You are an expert Wealth Management Assistant reporting to a Financial Associate. "
            "Your job is to read the raw data gathered by the internal system in the chat history "
            "and synthesize it into a clean, beautifully formatted Markdown response that directly answers the user's initial prompt. "
            "CRITICAL: Never mention 'agents', 'tools', 'SQL', or the 'supervisor'. Speak naturally as the unified AI assistant. If no data was found, say so politely."
        )
        
        # 🛑 FIX: The "Dummy Human" Nudge for the Synthesizer
        messages_to_pass = list(state["messages"])
        if len(messages_to_pass) > 0 and messages_to_pass[-1].type != "human":
            nudge = HumanMessage(content="Please synthesize the data above into a final, professional response for the user.")
            messages_to_pass.append(nudge)
        
        print(f"\n📝 [SYNTHESIZER] Formatting final response for associate...")
        response = llm.invoke([SystemMessage(content=system_prompt)] + messages_to_pass)
        return {"messages": [response]}

    builder.add_node("supervisor", supervisor)
    builder.add_node("synthesizer", synthesizer)

    # 🗺️ Logic: Always return to supervisor after a worker finishes
    for name in ['client_profile_domain_agent', 'portfolio_domain_agent', 'interactions_domain_agent', 'compliance_documents_domain_agent', 'email_communications_domain_agent']:
        builder.add_edge(name, "supervisor")

    # 🏁 Logic: Supervisor routes to Synthesizer on FINISH
    def should_continue(state: WF_001State):
        if state["next_node"] == "FINISH":
            return "synthesizer"
        return state["next_node"]

    builder.add_conditional_edges("supervisor", should_continue)
    builder.add_edge("synthesizer", END)
    builder.add_edge(START, "supervisor")

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)

if __name__ == "__main__":
    print("🎉 Successfully compiled Domain Supervisor graph with Synthesis.")
