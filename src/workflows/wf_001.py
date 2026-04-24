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
    interaction_summarizer_agent_cfg = registry_manager.agents.get('interaction_summarizer_agent')
    workflow.add_node('interaction_summarizer_agent', factory.build_node(interaction_summarizer_agent_cfg))
    estate_planning_synthesis_agent_cfg = registry_manager.agents.get('estate_planning_synthesis_agent')
    workflow.add_node('estate_planning_synthesis_agent', factory.build_node(estate_planning_synthesis_agent_cfg))
    balance_growth_analysis_agent_cfg = registry_manager.agents.get('balance_growth_analysis_agent')
    workflow.add_node('balance_growth_analysis_agent', factory.build_node(balance_growth_analysis_agent_cfg))
    financial_plan_review_checker_agent_cfg = registry_manager.agents.get('financial_plan_review_checker_agent')
    workflow.add_node('financial_plan_review_checker_agent', factory.build_node(financial_plan_review_checker_agent_cfg))
    meeting_prep_agent_cfg = registry_manager.agents.get('meeting_prep_agent')
    workflow.add_node('meeting_prep_agent', factory.build_node(meeting_prep_agent_cfg))
    client_profile_sql_agent_cfg = registry_manager.agents.get('client_profile_sql_agent')
    workflow.add_node('client_profile_sql_agent', factory.build_node(client_profile_sql_agent_cfg))
    nba_agent_cfg = registry_manager.agents.get('nba_agent')
    workflow.add_node('nba_agent', factory.build_node(nba_agent_cfg))
    schema_discovery_agent_cfg = registry_manager.agents.get('schema_discovery_agent')
    workflow.add_node('schema_discovery_agent', factory.build_node(schema_discovery_agent_cfg))
    life_events_news_agent_cfg = registry_manager.agents.get('life_events_news_agent')
    workflow.add_node('life_events_news_agent', factory.build_node(life_events_news_agent_cfg))
    life_event_detector_agent_cfg = registry_manager.agents.get('life_event_detector_agent')
    workflow.add_node('life_event_detector_agent', factory.build_node(life_event_detector_agent_cfg))
    synthesis_agent_cfg = registry_manager.agents.get('synthesis_agent')
    workflow.add_node('synthesis_agent', factory.build_node(synthesis_agent_cfg))
    tax_document_sql_agent_cfg = registry_manager.agents.get('tax_document_sql_agent')
    workflow.add_node('tax_document_sql_agent', factory.build_node(tax_document_sql_agent_cfg))
    sentiment_agent_cfg = registry_manager.agents.get('sentiment_agent')
    workflow.add_node('sentiment_agent', factory.build_node(sentiment_agent_cfg))
    compliance_agent_cfg = registry_manager.agents.get('compliance_agent')
    workflow.add_node('compliance_agent', factory.build_node(compliance_agent_cfg))
    tax_document_synthesis_agent_cfg = registry_manager.agents.get('tax_document_synthesis_agent')
    workflow.add_node('tax_document_synthesis_agent', factory.build_node(tax_document_synthesis_agent_cfg))
    financial_planning_agent_cfg = registry_manager.agents.get('financial_planning_agent')
    workflow.add_node('financial_planning_agent', factory.build_node(financial_planning_agent_cfg))

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
            "Identify clients with unaddressed life events": ['life_event_detector_agent', 'financial_plan_review_checker_agent'],
            "Identify aging estate plans for wealthy older clients": ['client_profile_sql_agent'],
            "Compare top clients across multiple dimensions": ['client_info_agent', 'financial_planning_agent', 'sentiment_agent', 'compliance_agent'],
            "Generate meeting prep summary": [],
            "Summarize recent interactions and follow-ups": ['interaction_summarizer_agent'],
            "Identify missing documents for upcoming meetings": ['compliance_agent', 'meeting_prep_agent'],
            "Identify outstanding tax documents": ['schema_discovery_agent'],
        }
        
        targets = routing_map.get(intent, [END])
        print(f"   🚀 [MASTER ROUTER]: Firing parallel workers -> {targets}\n")
        return targets

    # Connect START to our LLM Router
    possible_targets = ['client_info_agent', 'interaction_summarizer_agent', 'estate_planning_synthesis_agent', 'balance_growth_analysis_agent', 'financial_plan_review_checker_agent', 'meeting_prep_agent', 'client_profile_sql_agent', 'nba_agent', 'schema_discovery_agent', 'life_events_news_agent', 'life_event_detector_agent', 'synthesis_agent', 'tax_document_sql_agent', 'sentiment_agent', 'compliance_agent', 'tax_document_synthesis_agent', 'financial_planning_agent'] + [END]
    workflow.add_conditional_edges(START, semantic_router, possible_targets)
    
    # Internal DAG Edges
    workflow.add_edge('life_event_detector_agent', 'synthesis_agent')
    workflow.add_edge('financial_plan_review_checker_agent', 'synthesis_agent')
    workflow.add_edge('synthesis_agent', END)
    workflow.add_edge('client_profile_sql_agent', 'balance_growth_analysis_agent')
    workflow.add_edge('client_profile_sql_agent', 'life_events_news_agent')
    workflow.add_edge('balance_growth_analysis_agent', 'estate_planning_synthesis_agent')
    workflow.add_edge('life_events_news_agent', 'estate_planning_synthesis_agent')
    workflow.add_edge('estate_planning_synthesis_agent', END)
    workflow.add_edge('client_info_agent', 'nba_agent')
    workflow.add_edge('financial_planning_agent', 'nba_agent')
    workflow.add_edge('sentiment_agent', 'nba_agent')
    workflow.add_edge('compliance_agent', 'nba_agent')
    workflow.add_edge('nba_agent', END)
    workflow.add_edge('interaction_summarizer_agent', END)
    workflow.add_edge('compliance_agent', 'synthesis_agent')
    workflow.add_edge('meeting_prep_agent', 'synthesis_agent')
    workflow.add_edge('synthesis_agent', END)
    workflow.add_edge('schema_discovery_agent', 'tax_document_sql_agent')
    workflow.add_edge('tax_document_sql_agent', 'tax_document_synthesis_agent')
    workflow.add_edge('tax_document_synthesis_agent', END)


    return workflow.compile()
