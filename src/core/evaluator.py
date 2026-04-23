# src/core/evaluator.py
import os
from pydantic import BaseModel, Field
from typing import Literal
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

class EvaluationResult(BaseModel):
    status: Literal["PASS", "FAIL"] = Field(
        ..., 
        description="PASS if the answer is 100% grounded in the logs. FAIL if there is any hallucination or internal knowledge leakage."
    )
    reason: str = Field(
        default="The critic flagged a failure but did not provide a specific reason.", 
        description="A detailed explanation of the attribution check. You MUST provide a detailed text explanation here."
    )

class GroundingCritic:
    def __init__(self): 
        model_id = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
        
        self.llm = ChatBedrock(
            model_id=model_id,
            region_name="us-east-1",
            temperature=0.0
        ).with_structured_output(EvaluationResult)

        self.static_system_prompt = """You are an uncompromising Compliance Auditor for AEON Wealth Management.
Your exclusive job is to perform a strict "3-Way Match" to verify AI Agent Attribution and prevent hallucination (Internal Knowledge Leakage).

THE RULES OF EVALUATION:
1. You will receive: The User's Question, the Raw Tool Logs (Data retrieved by the agent), and the Agent's Final Answer.
2. You must trace EVERY factual claim, financial number, percentage, tax rate, and recommendation in the Agent's Final Answer back to the Raw Tool Logs.
3. If the Agent's Final Answer contains ANY fact, assumption, or financial rule that is NOT explicitly present in the Raw Tool Logs, you MUST FAIL the agent.
4. Admitting a lack of information (e.g., "The data does not state the tax implications") is safe and should PASS.
5. Relying on pre-trained internal knowledge (e.g., quoting standard IRS tax rates, assuming standard market rules) is a critical compliance violation and MUST FAIL.
6. NEGATIVE COMPLIANCE: If the agent encounters missing data for a requested entity, it MUST halt. Adapting via fuzzy matching or assuming a different entity is a critical violation and MUST FAIL.
7. CRITICAL OUTPUT RULE: You MUST return a JSON object containing BOTH 'status' and 'reason'. Never leave the reason blank."""

    def evaluate(self, user_question: str, tool_logs: str, agent_answer: str) -> EvaluationResult:
        dynamic_content = f"""Please perform the 3-Way Match Evaluation on the following:

--- 1. USER QUESTION ---
{user_question}

--- 2. RAW TOOL LOGS ---
{tool_logs}

--- 3. AGENT'S FINAL ANSWER ---
{agent_answer}
"""
        messages = [
            SystemMessage(content=self.static_system_prompt),
            HumanMessage(content=dynamic_content)
        ]
        
        return self.llm.invoke(messages)