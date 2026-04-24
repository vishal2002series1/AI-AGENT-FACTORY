# src/scripts/batch_autofabricator.py
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.core.sandbox import SandboxOrchestrator

def run_batch_fabrication(workflow_file_name: str):
    base_dir = os.path.dirname(__file__)
    workflow_path = os.path.abspath(os.path.join(base_dir, f'../../workflows/{workflow_file_name}'))
    
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)

    print(f"🚀 Starting Batch Autofabricator for: {workflow['workflow_name']}")
    orchestrator = SandboxOrchestrator()

    final_edges = []
    compiled_agents = set()

    for q in workflow["target_questions"]:
        print(f"\n⚙️ PROCESSING TARGET: {q['id']} - {q['prompt']}")
        
        # Sandbox now returns the agent names AND the mathematical DAG!
        result = orchestrator.run_workflow_builder(q["prompt"])
        
        # 🛑 FIX: Safely unpack the tuple without skipping on empty lists
        if result and len(result) == 2:
            agent_names, edges = result
            
            # Since sandbox returns strings, we can safely add them directly
            for a_name in agent_names:
                compiled_agents.add(a_name)
                
            for e in edges:
                final_edges.append({"source": e.source, "target": e.target})
            
    # Save the declarative DAG JSON for the compiler
    dag_path = os.path.abspath(os.path.join(base_dir, f'../../workflows/{workflow["workflow_id"]}_dag.json'))
    
    # Optional: Deduplicate edges just in case
    unique_edges = [dict(t) for t in {tuple(d.items()) for d in final_edges}]
    
    with open(dag_path, 'w') as f:
        json.dump({"workflow_id": workflow["workflow_id"], "agents": list(compiled_agents), "edges": unique_edges}, f, indent=2)
        
    print(f"\n🎉 Saved Declarative DAG to {dag_path}!")

if __name__ == "__main__":
    run_batch_fabrication('workflow_1_client_prep.json')