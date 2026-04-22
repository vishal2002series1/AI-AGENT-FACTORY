# test_sandbox.py
from src.core.sandbox import SandboxOrchestrator

orchestrator = SandboxOrchestrator()

# The user requests a complex workflow that our baseline agents aren't optimized for.
test_query = "What are the tax implications if Emily Chen sells her NVDA stock?"

orchestrator.run_workflow_builder(test_query)