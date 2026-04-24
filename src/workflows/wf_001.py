# AUTO-COMPILED WORKFLOW: WF_001
import operator
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from src.agents.config import registry_manager
from src.agents.factory import AgentFactory

class WF_001State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: Annotated[list[str], operator.add]

def build_WF_001_graph():
    factory = AgentFactory()
    workflow = StateGraph(WF_001State)
    
    client_info_agent_cfg = registry_manager.agents.get('client_info_agent')
    workflow.add_node('client_info_agent', factory.build_node(client_info_agent_cfg))
    interaction_summarizer_agent_cfg = registry_manager.agents.get('interaction_summarizer_agent')
    workflow.add_node('interaction_summarizer_agent', factory.build_node(interaction_summarizer_agent_cfg))
    life_event_detector_agent_cfg = registry_manager.agents.get('life_event_detector_agent')
    workflow.add_node('life_event_detector_agent', factory.build_node(life_event_detector_agent_cfg))
    nba_agent_cfg = registry_manager.agents.get('nba_agent')
    workflow.add_node('nba_agent', factory.build_node(nba_agent_cfg))
    portfolio_analytics_agent_cfg = registry_manager.agents.get('portfolio_analytics_agent')
    workflow.add_node('portfolio_analytics_agent', factory.build_node(portfolio_analytics_agent_cfg))
    synthesis_agent_cfg = registry_manager.agents.get('synthesis_agent')
    workflow.add_node('synthesis_agent', factory.build_node(synthesis_agent_cfg))
    sentiment_agent_cfg = registry_manager.agents.get('sentiment_agent')
    workflow.add_node('sentiment_agent', factory.build_node(sentiment_agent_cfg))
    financial_planning_agent_cfg = registry_manager.agents.get('financial_planning_agent')
    workflow.add_node('financial_planning_agent', factory.build_node(financial_planning_agent_cfg))
    meeting_prep_agent_cfg = registry_manager.agents.get('meeting_prep_agent')
    workflow.add_node('meeting_prep_agent', factory.build_node(meeting_prep_agent_cfg))
    financial_plan_review_checker_agent_cfg = registry_manager.agents.get('financial_plan_review_checker_agent')
    workflow.add_node('financial_plan_review_checker_agent', factory.build_node(financial_plan_review_checker_agent_cfg))
    compliance_agent_cfg = registry_manager.agents.get('compliance_agent')
    workflow.add_node('compliance_agent', factory.build_node(compliance_agent_cfg))

    # Declarative Routing
    workflow.add_edge(START, 'meeting_prep_agent')
    workflow.add_edge(START, 'financial_planning_agent')
    workflow.add_edge(START, 'client_info_agent')
    workflow.add_edge(START, 'portfolio_analytics_agent')
    workflow.add_edge('financial_planning_agent', 'client_info_agent')
    workflow.add_edge('financial_plan_review_checker_agent', 'synthesis_agent')
    workflow.add_edge('life_event_detector_agent', 'client_info_agent')
    workflow.add_edge('financial_planning_agent', 'nba_agent')
    workflow.add_edge(START, 'compliance_agent')
    workflow.add_edge('portfolio_analytics_agent', 'nba_agent')
    workflow.add_edge('client_info_agent', 'nba_agent')
    workflow.add_edge(START, 'life_event_detector_agent')
    workflow.add_edge('compliance_agent', 'nba_agent')
    workflow.add_edge(START, 'interaction_summarizer_agent')
    workflow.add_edge('synthesis_agent', END)
    workflow.add_edge(START, 'sentiment_agent')
    workflow.add_edge('sentiment_agent', 'nba_agent')
    workflow.add_edge('interaction_summarizer_agent', END)
    workflow.add_edge('meeting_prep_agent', 'synthesis_agent')
    workflow.add_edge('life_event_detector_agent', 'synthesis_agent')
    workflow.add_edge('client_info_agent', END)
    workflow.add_edge('compliance_agent', 'synthesis_agent')
    workflow.add_edge(START, 'financial_plan_review_checker_agent')
    workflow.add_edge('compliance_agent', END)
    workflow.add_edge('nba_agent', END)

    return workflow.compile()
