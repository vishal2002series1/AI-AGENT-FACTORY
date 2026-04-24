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

    compiled_agents = set()
    intents_map = {}

    for q in workflow["target_questions"]:
        print(f"\n⚙️ PROCESSING TARGET: {q['id']} - {q['prompt']}")
        
        intent = q["intent"]
        result = orchestrator.run_workflow_builder(q["prompt"])
        
        if result and len(result) == 2:
            agent_names, edges = result
            
            for a_name in agent_names:
                compiled_agents.add(a_name)
            
            # Map edges specific to this intent
            intent_edges = []
            for e in edges:
                intent_edges.append({"source": e.source, "target": e.target})
                
            intents_map[intent] = intent_edges
            
    dag_path = os.path.abspath(os.path.join(base_dir, f'../../workflows/{workflow["workflow_id"]}_dag.json'))
    
    with open(dag_path, 'w') as f:
        json.dump({
            "workflow_id": workflow["workflow_id"], 
            "agents": list(compiled_agents), 
            "intents": intents_map
        }, f, indent=2)
        
    print(f"\n🎉 Saved Intent-Driven Declarative DAG to {dag_path}!")

if __name__ == "__main__":
    run_batch_fabrication('workflow_1_client_prep.json')