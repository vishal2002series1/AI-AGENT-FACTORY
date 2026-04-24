# test_compiled_workflow.py
import time
import uuid
import json
import os
from langchain_core.messages import HumanMessage

# Import the new WF_001 graph!
from src.workflows.wf_001 import build_WF_001_graph

def run_performance_test():
    print("🚀 Loading Compiled Workflow (WF_001)...")
    app = build_WF_001_graph()
    
    # Load questions dynamically from the JSON
    base_dir = os.path.dirname(__file__)
    workflow_path = os.path.abspath(os.path.join(base_dir, 'workflows/workflow_1_client_prep.json'))
    
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
        
    queries = [q["prompt"] for q in workflow["target_questions"]]
    
    for i, query in enumerate(queries, 1):
        print("\n" + "═"*80)
        print(f"🎯 EXECUTING QUESTION {i}/{len(queries)}")
        print(f"❓ {query}")
        print("═"*80)
        
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        print("⏳ Running static graph...")
        start_time = time.time()
        
        final_answer = ""
        # Capture the answer directly from the stream
        for event in app.stream({"messages": [HumanMessage(content=query)]}, config=config, stream_mode="updates"):
            for node_name, node_data in event.items():
                print(f"  🟢 [NODE COMPLETED]: '{node_name}' finished its task.")
                # We extract the last message from the node to get the final synthesis output
                if "messages" in node_data and len(node_data["messages"]) > 0:
                    final_answer = node_data["messages"][-1].content
                    
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n⏱️ EXECUTION TIME: {execution_time:.2f} seconds")
        print("\n📝 [FINAL ANSWER]:")
        print(final_answer)
        print("-" * 80)
        
        # Optional: Add a slight pause between heavy queries so we don't hit rate limits
        time.sleep(2)

if __name__ == "__main__":
    run_performance_test()