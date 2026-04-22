# test_graph.py
from src.agents.graph import aeon_app
from langchain_core.messages import HumanMessage
from langgraph.types import Command

config = {"configurable": {"thread_id": "advisor_session_2000"}}

# A complex query requiring multiple agents!
complex_query = """
Review Emily Chen's profile. 
1. Is she showing any flight risk or negative sentiment in recent communications? 
2. What is her exposure to NVDA, and is it a concentration risk based on cost basis?
"""

inputs = {"messages": [HumanMessage(content=complex_query)]}

print("Running Enterprise Aeon Factory Workflow...\n")
for event in aeon_app.stream(inputs, config=config, stream_mode="values"):
    if "routing_log" in event and event["routing_log"]:
        print(f"🧭 [Supervisor Decision]: {event['routing_log'][-1]}")
    elif "messages" in event and event["messages"]:
        print(f"💬 [Message]: {event['messages'][-1].content[:150]}...\n")

# Handling interrupts (if any)
state = aeon_app.get_state(config)
if state.next:
    print("\n--- 🛑 GRAPH PAUSED FOR HUMAN INPUT ---")
    human_input = input("Provide Clarification: ")
    print("\nResuming workflow...")
    for event in aeon_app.stream(Command(resume=human_input), config=config, stream_mode="values"):
        if "routing_log" in event and event["routing_log"]:
            print(f"🧭 [Supervisor Decision]: {event['routing_log'][-1]}")
        elif "messages" in event and event["messages"]:
            print(f"💬 [Message]: {event['messages'][-1].content[:150]}...\n")