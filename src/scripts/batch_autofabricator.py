# src/scripts/batch_autofabricator.py
import json
import os
import sys

# Ensure Python can find the src directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.core.sandbox import SandboxOrchestrator

def run_batch_fabrication():
    # 1. Locate the JSON workflow definition
    base_dir = os.path.dirname(__file__)
    workflow_path = os.path.abspath(os.path.join(base_dir, '../../workflows/workflow_1_client_prep.json'))
    
    if not os.path.exists(workflow_path):
        print(f"❌ Error: Could not find {workflow_path}")
        return

    # 2. Load the Requirements
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)

    print(f"🚀 Starting Batch Autofabricator for: {workflow['workflow_name']}")
    print(f"📂 Data Sources Required: {', '.join(workflow['required_data_sources'])}")
    
    orchestrator = SandboxOrchestrator()

    # 3. Loop through every question and send it through the Sandbox
    for q in workflow["target_questions"]:
        print("\n" + "═"*80)
        print(f"⚙️ PROCESSING TARGET: {q['id']} - {q['intent']}")
        print(f"❓ PROMPT: {q['prompt']}")
        print("═"*80)
        
        # The Sandbox automatically handles the Dry Run, Fabrication, and Validation!
        orchestrator.run_workflow_builder(q["prompt"])

    print(f"\n🎉 Batch Fabrication for '{workflow['workflow_name']}' is complete!")
    print("Check data_local/agent_registry.json to see your newly minted agents.")

if __name__ == "__main__":
    run_batch_fabrication()