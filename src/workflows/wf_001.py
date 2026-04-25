# AUTO-COMPILED SEMANTIC WORKFLOW: WF_001
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

class WF_001State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: Annotated[list[str], operator.add]

# 🧠 Auto-Generated Semantic Classifier Schema
class IntentClassification(BaseModel):
    intent: Literal["Identify clients with unaddressed life events", "Identify aging estate plans for wealthy older clients", "Compare top clients across multiple dimensions", "Generate meeting prep summary", "Summarize recent interactions and follow-ups", "Identify missing documents for upcoming meetings", "Identify outstanding tax documents", "General conversational follow-up and ad-hoc queries", "UNKNOWN"] = Field(
        ..., 
        description="Classify the user's query into one of these exact intents based on the conversation history."
    )

def build_WF_001_graph():
    factory = AgentFactory()
    workflow = StateGraph(WF_001State)
    

    meeting_prep_synthesis_agent_cfg = registry_manager.agents.get('meeting_prep_synthesis_agent')
    if not meeting_prep_synthesis_agent_cfg:
        print(f"⚠️  WARNING: Agent 'meeting_prep_synthesis_agent' was in DAG but not registry. Creating default fallback.")
        meeting_prep_synthesis_agent_cfg = AgentConfig(
            name='meeting_prep_synthesis_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('meeting_prep_synthesis_agent', factory.build_node(meeting_prep_synthesis_agent_cfg))

    compliance_agent_cfg = registry_manager.agents.get('compliance_agent')
    if not compliance_agent_cfg:
        print(f"⚠️  WARNING: Agent 'compliance_agent' was in DAG but not registry. Creating default fallback.")
        compliance_agent_cfg = AgentConfig(
            name='compliance_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('compliance_agent', factory.build_node(compliance_agent_cfg))

    financial_planning_agent_cfg = registry_manager.agents.get('financial_planning_agent')
    if not financial_planning_agent_cfg:
        print(f"⚠️  WARNING: Agent 'financial_planning_agent' was in DAG but not registry. Creating default fallback.")
        financial_planning_agent_cfg = AgentConfig(
            name='financial_planning_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('financial_planning_agent', factory.build_node(financial_planning_agent_cfg))

    interaction_summarizer_agent_cfg = registry_manager.agents.get('interaction_summarizer_agent')
    if not interaction_summarizer_agent_cfg:
        print(f"⚠️  WARNING: Agent 'interaction_summarizer_agent' was in DAG but not registry. Creating default fallback.")
        interaction_summarizer_agent_cfg = AgentConfig(
            name='interaction_summarizer_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('interaction_summarizer_agent', factory.build_node(interaction_summarizer_agent_cfg))

    interaction_research_agent_cfg = registry_manager.agents.get('interaction_research_agent')
    if not interaction_research_agent_cfg:
        print(f"⚠️  WARNING: Agent 'interaction_research_agent' was in DAG but not registry. Creating default fallback.")
        interaction_research_agent_cfg = AgentConfig(
            name='interaction_research_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('interaction_research_agent', factory.build_node(interaction_research_agent_cfg))

    portfolio_analytics_agent_cfg = registry_manager.agents.get('portfolio_analytics_agent')
    if not portfolio_analytics_agent_cfg:
        print(f"⚠️  WARNING: Agent 'portfolio_analytics_agent' was in DAG but not registry. Creating default fallback.")
        portfolio_analytics_agent_cfg = AgentConfig(
            name='portfolio_analytics_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('portfolio_analytics_agent', factory.build_node(portfolio_analytics_agent_cfg))

    transaction_monitor_agent_cfg = registry_manager.agents.get('transaction_monitor_agent')
    if not transaction_monitor_agent_cfg:
        print(f"⚠️  WARNING: Agent 'transaction_monitor_agent' was in DAG but not registry. Creating default fallback.")
        transaction_monitor_agent_cfg = AgentConfig(
            name='transaction_monitor_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('transaction_monitor_agent', factory.build_node(transaction_monitor_agent_cfg))

    portfolio_concentration_agent_cfg = registry_manager.agents.get('portfolio_concentration_agent')
    if not portfolio_concentration_agent_cfg:
        print(f"⚠️  WARNING: Agent 'portfolio_concentration_agent' was in DAG but not registry. Creating default fallback.")
        portfolio_concentration_agent_cfg = AgentConfig(
            name='portfolio_concentration_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('portfolio_concentration_agent', factory.build_node(portfolio_concentration_agent_cfg))

    meeting_prep_agent_cfg = registry_manager.agents.get('meeting_prep_agent')
    if not meeting_prep_agent_cfg:
        print(f"⚠️  WARNING: Agent 'meeting_prep_agent' was in DAG but not registry. Creating default fallback.")
        meeting_prep_agent_cfg = AgentConfig(
            name='meeting_prep_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('meeting_prep_agent', factory.build_node(meeting_prep_agent_cfg))

    client_query_agent_cfg = registry_manager.agents.get('client_query_agent')
    if not client_query_agent_cfg:
        print(f"⚠️  WARNING: Agent 'client_query_agent' was in DAG but not registry. Creating default fallback.")
        client_query_agent_cfg = AgentConfig(
            name='client_query_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('client_query_agent', factory.build_node(client_query_agent_cfg))

    synthesis_agent_cfg = registry_manager.agents.get('synthesis_agent')
    if not synthesis_agent_cfg:
        print(f"⚠️  WARNING: Agent 'synthesis_agent' was in DAG but not registry. Creating default fallback.")
        synthesis_agent_cfg = AgentConfig(
            name='synthesis_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('synthesis_agent', factory.build_node(synthesis_agent_cfg))

    client_data_agent_cfg = registry_manager.agents.get('client_data_agent')
    if not client_data_agent_cfg:
        print(f"⚠️  WARNING: Agent 'client_data_agent' was in DAG but not registry. Creating default fallback.")
        client_data_agent_cfg = AgentConfig(
            name='client_data_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('client_data_agent', factory.build_node(client_data_agent_cfg))

    client_info_agent_cfg = registry_manager.agents.get('client_info_agent')
    if not client_info_agent_cfg:
        print(f"⚠️  WARNING: Agent 'client_info_agent' was in DAG but not registry. Creating default fallback.")
        client_info_agent_cfg = AgentConfig(
            name='client_info_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('client_info_agent', factory.build_node(client_info_agent_cfg))

    nba_agent_cfg = registry_manager.agents.get('nba_agent')
    if not nba_agent_cfg:
        print(f"⚠️  WARNING: Agent 'nba_agent' was in DAG but not registry. Creating default fallback.")
        nba_agent_cfg = AgentConfig(
            name='nba_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('nba_agent', factory.build_node(nba_agent_cfg))

    life_event_transcript_agent_cfg = registry_manager.agents.get('life_event_transcript_agent')
    if not life_event_transcript_agent_cfg:
        print(f"⚠️  WARNING: Agent 'life_event_transcript_agent' was in DAG but not registry. Creating default fallback.")
        life_event_transcript_agent_cfg = AgentConfig(
            name='life_event_transcript_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('life_event_transcript_agent', factory.build_node(life_event_transcript_agent_cfg))

    transcript_search_agent_cfg = registry_manager.agents.get('transcript_search_agent')
    if not transcript_search_agent_cfg:
        print(f"⚠️  WARNING: Agent 'transcript_search_agent' was in DAG but not registry. Creating default fallback.")
        transcript_search_agent_cfg = AgentConfig(
            name='transcript_search_agent',
            routing_description='Fallback agent for missing registry entry',
            persona='You are a fallback agent. Acknowledge the query and state that your specific tools were not loaded.',
            model_id='us.anthropic.claude-sonnet-4-6',
            authorized_tools=[],
            temperature=0.0
        )
    workflow.add_node('transcript_search_agent', factory.build_node(transcript_search_agent_cfg))

    # 🔀 Semantic Intent Router Node with Conversational Memory
    def semantic_router(state: WF_001State) -> list[str]:
        model_id = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
        llm = ChatBedrock(model_id=model_id, region_name="us-east-1", temperature=0.0)
        classifier = llm.with_structured_output(IntentClassification)
        
        # Fetch the last 4 messages to give the router conversational context
        recent_messages = state["messages"][-4:]
        chat_history = "\n".join([f"{m.type}: {m.content}" for m in recent_messages])
        
        try:
            classification = classifier.invoke([
                {"role": "system", "content": "You are a Semantic Intent Router for a Wealth Management platform. Read the conversation history and classify the LATEST user intent. If it's a follow-up question, pick 'General conversational follow-up and ad-hoc queries'. If it matches nothing, select UNKNOWN."},
                {"role": "user", "content": f"Conversation History:\n{chat_history}" }
            ])
            intent = classification.intent
        except Exception as e:
            print(f"      ⚠️ Router Classification Failed: {e}")
            intent = "UNKNOWN"
            
        print(f"\n   🔀 [MASTER ROUTER]: Classified Intent -> '{intent}'")
        
        routing_map = {
            "Identify clients with unaddressed life events": [],
            "Identify aging estate plans for wealthy older clients": ['life_event_transcript_agent', 'financial_planning_agent', 'portfolio_analytics_agent'],
            "Compare top clients across multiple dimensions": ['portfolio_analytics_agent', 'client_info_agent', 'nba_agent', 'compliance_agent', 'interaction_summarizer_agent'],
            "Generate meeting prep summary": ['client_data_agent', 'transaction_monitor_agent', 'portfolio_concentration_agent', 'interaction_research_agent'],
            "Summarize recent interactions and follow-ups": ['interaction_summarizer_agent'],
            "Identify missing documents for upcoming meetings": ['compliance_agent', 'meeting_prep_agent'],
            "Identify outstanding tax documents": ['compliance_agent'],
            "General conversational follow-up and ad-hoc queries": ['client_query_agent'],
        }
        
        # If UNKNOWN, route to the Fallback Agent instead of END
        targets = routing_map.get(intent)
        if not targets or intent == "UNKNOWN":
            targets = routing_map.get("General conversational follow-up and ad-hoc queries", [END])
            
        print(f"   🚀 [MASTER ROUTER]: Firing parallel workers -> {targets}\n")
        return targets

    # Connect START to our LLM Router
    possible_targets = ['meeting_prep_synthesis_agent', 'compliance_agent', 'financial_planning_agent', 'interaction_summarizer_agent', 'interaction_research_agent', 'portfolio_analytics_agent', 'transaction_monitor_agent', 'portfolio_concentration_agent', 'meeting_prep_agent', 'client_query_agent', 'synthesis_agent', 'client_data_agent', 'client_info_agent', 'nba_agent', 'life_event_transcript_agent', 'transcript_search_agent'] + [END]
    workflow.add_conditional_edges(START, semantic_router, possible_targets)
    
    # Internal DAG Edges
    workflow.add_edge('life_event_transcript_agent', 'synthesis_agent')
    workflow.add_edge('financial_planning_agent', 'synthesis_agent')
    workflow.add_edge('portfolio_analytics_agent', 'synthesis_agent')
    workflow.add_edge('synthesis_agent', END)
    workflow.add_edge('portfolio_analytics_agent', 'synthesis_agent')
    workflow.add_edge('client_info_agent', 'synthesis_agent')
    workflow.add_edge('nba_agent', 'synthesis_agent')
    workflow.add_edge('compliance_agent', 'synthesis_agent')
    workflow.add_edge('interaction_summarizer_agent', 'synthesis_agent')
    workflow.add_edge('synthesis_agent', END)
    workflow.add_edge('client_data_agent', 'meeting_prep_synthesis_agent')
    workflow.add_edge('transaction_monitor_agent', 'meeting_prep_synthesis_agent')
    workflow.add_edge('portfolio_concentration_agent', 'meeting_prep_synthesis_agent')
    workflow.add_edge('interaction_research_agent', 'meeting_prep_synthesis_agent')
    workflow.add_edge('meeting_prep_synthesis_agent', END)
    workflow.add_edge('interaction_summarizer_agent', END)
    workflow.add_edge('compliance_agent', 'synthesis_agent')
    workflow.add_edge('meeting_prep_agent', 'synthesis_agent')
    workflow.add_edge('synthesis_agent', END)
    workflow.add_edge('compliance_agent', END)
    workflow.add_edge('client_query_agent', 'transcript_search_agent')
    workflow.add_edge('transcript_search_agent', 'synthesis_agent')
    workflow.add_edge('synthesis_agent', END)


    # Attach MemorySaver to persist state across chat turns
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
