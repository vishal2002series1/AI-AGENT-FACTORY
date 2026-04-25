# AUTO-COMPILED SEMANTIC WORKFLOW: WF_001
import os
import operator
from typing import Annotated, Sequence, TypedDict, Literal
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_aws import ChatBedrock
from pydantic import BaseModel, Field

from src.agents.config import registry_manager
from src.agents.factory import AgentFactory

class WF_001State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: Annotated[list[str], operator.add]

# 🧠 Auto-Generated Semantic Classifier Schema
class IntentClassification(BaseModel):
    intent: Literal["Identify clients with unaddressed life events", "Identify aging estate plans for wealthy older clients", "Compare top clients across multiple dimensions", "Generate meeting prep summary", "Summarize recent interactions and follow-ups", "Identify missing documents for upcoming meetings", "Identify outstanding tax documents", "UNKNOWN"] = Field(
        ..., 
        description="Classify the user's financial query into one of these exact intents."
    )

def build_WF_001_graph():
    factory = AgentFactory()
    workflow = StateGraph(WF_001State)
    
    client_info_agent_cfg = registry_manager.agents.get('client_info_agent')
    workflow.add_node('client_info_agent', factory.build_node(client_info_agent_cfg))
    portfolio_analytics_agent_cfg = registry_manager.agents.get('portfolio_analytics_agent')
    workflow.add_node('portfolio_analytics_agent', factory.build_node(portfolio_analytics_agent_cfg))
    compliance_agent_cfg = registry_manager.agents.get('compliance_agent')
    workflow.add_node('compliance_agent', factory.build_node(compliance_agent_cfg))
    synthesis_agent_cfg = registry_manager.agents.get('synthesis_agent')
    workflow.add_node('synthesis_agent', factory.build_node(synthesis_agent_cfg))
    nba_agent_cfg = registry_manager.agents.get('nba_agent')
    workflow.add_node('nba_agent', factory.build_node(nba_agent_cfg))
    meeting_prep_agent_cfg = registry_manager.agents.get('meeting_prep_agent')
    workflow.add_node('meeting_prep_agent', factory.build_node(meeting_prep_agent_cfg))
    financial_planning_agent_cfg = registry_manager.agents.get('financial_planning_agent')
    workflow.add_node('financial_planning_agent', factory.build_node(financial_planning_agent_cfg))
    interaction_summarizer_agent_cfg = registry_manager.agents.get('interaction_summarizer_agent')
    workflow.add_node('interaction_summarizer_agent', factory.build_node(interaction_summarizer_agent_cfg))

    # 🔀 Semantic Intent Router Node
    def semantic_router(state: WF_001State) -> list[str]:
        # Using a fast/cheap model for routing
        model_id = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
        llm = ChatBedrock(model_id=model_id, region_name="us-east-1", temperature=0.0)
        classifier = llm.with_structured_output(IntentClassification)
        
        last_message = state["messages"][-1].content
        
        try:
            classification = classifier.invoke([
                {"role": "system", "content": "You are a Semantic Intent Router for a Wealth Management platform. Read the user's query and classify it. If it doesn't match perfectly, select UNKNOWN."},
                {"role": "user", "content": last_message}
            ])
            intent = classification.intent
        except Exception as e:
            print(f"      ⚠️ Router Classification Failed: {e}")
            intent = "UNKNOWN"
            
        print(f"\n   🔀 [MASTER ROUTER]: Classified Intent -> '{intent}'")
        
        routing_map = {
            "Identify clients with unaddressed life events": ['meeting_prep_agent', 'financial_planning_agent'],
            "Identify aging estate plans for wealthy older clients": ['client_info_agent', 'portfolio_analytics_agent', 'financial_planning_agent'],
            "Compare top clients across multiple dimensions": ['client_info_agent', 'financial_planning_agent', 'portfolio_analytics_agent', 'compliance_agent', 'interaction_summarizer_agent', 'nba_agent'],
            "Generate meeting prep summary": ['meeting_prep_agent', 'portfolio_analytics_agent', 'compliance_agent', 'interaction_summarizer_agent'],
            "Summarize recent interactions and follow-ups": ['interaction_summarizer_agent'],
            "Identify missing documents for upcoming meetings": ['meeting_prep_agent', 'compliance_agent'],
            "Identify outstanding tax documents": ['compliance_agent'],
        }
        
        targets = routing_map.get(intent, [END])
        print(f"   🚀 [MASTER ROUTER]: Firing parallel workers -> {targets}\n")
        return targets

    # Connect START to our LLM Router
    possible_targets = ['client_info_agent', 'portfolio_analytics_agent', 'compliance_agent', 'synthesis_agent', 'nba_agent', 'meeting_prep_agent', 'financial_planning_agent', 'interaction_summarizer_agent'] + [END]
    workflow.add_conditional_edges(START, semantic_router, possible_targets)
    
    # Internal DAG Edges
    workflow.add_edge('meeting_prep_agent', 'synthesis_agent')
    workflow.add_edge('financial_planning_agent', 'synthesis_agent')
    workflow.add_edge('synthesis_agent', END)
    workflow.add_edge('client_info_agent', 'synthesis_agent')
    workflow.add_edge('portfolio_analytics_agent', 'synthesis_agent')
    workflow.add_edge('financial_planning_agent', 'synthesis_agent')
    workflow.add_edge('synthesis_agent', END)
    workflow.add_edge('client_info_agent', 'synthesis_agent')
    workflow.add_edge('financial_planning_agent', 'synthesis_agent')
    workflow.add_edge('portfolio_analytics_agent', 'synthesis_agent')
    workflow.add_edge('compliance_agent', 'synthesis_agent')
    workflow.add_edge('interaction_summarizer_agent', 'synthesis_agent')
    workflow.add_edge('nba_agent', 'synthesis_agent')
    workflow.add_edge('synthesis_agent', END)
    workflow.add_edge('meeting_prep_agent', 'interaction_summarizer_agent')
    workflow.add_edge('portfolio_analytics_agent', 'interaction_summarizer_agent')
    workflow.add_edge('compliance_agent', 'interaction_summarizer_agent')
    workflow.add_edge('interaction_summarizer_agent', END)
    workflow.add_edge('interaction_summarizer_agent', END)
    workflow.add_edge('meeting_prep_agent', 'synthesis_agent')
    workflow.add_edge('compliance_agent', 'synthesis_agent')
    workflow.add_edge('synthesis_agent', END)
    workflow.add_edge('compliance_agent', END)


    return workflow.compile()
