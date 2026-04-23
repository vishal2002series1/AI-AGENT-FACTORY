# test_compiled_workflow.py
import time
import uuid
from langchain_core.messages import HumanMessage

# Import your newly compiled shippable product!
from src.workflows.wf_001 import build_WF_001_graph

def run_performance_test():
    print("🚀 Loading Compiled Workflow (WF_001)...")
    app = build_WF_001_graph()
    
    queries = [
        "Which clients have had a major life event recently but no updated financial plan or scheduled review meeting?",
        "Which clients over 50 have estate planning documents that are more than 3 years old and have had significant balance growth or life changes since then?"
    ]
    
    for i, query in enumerate(queries, 1):
        print("\n" + "═"*80)
        print(f"🎯 EXECUTING QUESTION {i}")
        print(f"❓ {query}")
        print("═"*80)
        
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        print("⏳ Running static graph...")
        start_time = time.time()
        
        final_answer = ""
        # 🛑 FIX: Capture the answer directly from the stream!
        for event in app.stream({"messages": [HumanMessage(content=query)]}, config=config, stream_mode="updates"):
            for node_name, node_data in event.items():
                print(f"  🟢 [NODE COMPLETED]: '{node_name}' finished its task.")
                if "messages" in node_data and len(node_data["messages"]) > 0:
                    final_answer = node_data["messages"][-1].content
                    
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n⏱️ EXECUTION TIME: {execution_time:.2f} seconds")
        print("\n📝 [FINAL ANSWER]:")
        print(final_answer)
        print("-" * 80)

if __name__ == "__main__":
    run_performance_test()