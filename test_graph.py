# test_graph.py
from src.agents.graph import aeon_app
from langchain_core.messages import HumanMessage
from langgraph.types import Command

# 1. Start a persistent session
config = {"configurable": {"thread_id": "advisor_session_1001"}}

# 2. Ask an ambiguous question to trigger HITL
inputs = {"messages": [HumanMessage(content="Check if Emily is missing compliance documents.")]}

print("Running Aeon Factory Workflow...\n")
for event in aeon_app.stream(inputs, config=config, stream_mode="values"):
    # Check if key exists AND the list is not empty
    if "routing_log" in event and event["routing_log"]:
        print(f"🧭 [Supervisor Decision]: {event['routing_log'][-1]}")
    elif "messages" in event and event["messages"]:
        print(f"💬 [Message]: {event['messages'][-1].content[:100]}...\n")

# 3. Handle the Interrupt
state = aeon_app.get_state(config)
if state.next:  # This means the graph has paused!
    print("\n--- 🛑 GRAPH PAUSED FOR HUMAN INPUT ---")
    
    # In your eventual UI, this would be a chat input box. 
    human_input = input("Provide Clarification: ")
    
    # Resume the exact state with the human's answer!
    print("\nResuming workflow...")
    for event in aeon_app.stream(Command(resume=human_input), config=config, stream_mode="values"):
        if "routing_log" in event and event["routing_log"]:
            print(f"🧭 [Supervisor Decision]: {event['routing_log'][-1]}")
        elif "messages" in event and event["messages"]:
            print(f"💬 [Message]: {event['messages'][-1].content[:100]}...\n")