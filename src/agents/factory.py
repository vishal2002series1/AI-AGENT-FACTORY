# src/agents/factory.py
import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage
from src.agents.tools import AEON_TOOLS
from src.agents.config import AgentConfig
from langgraph.prebuilt import create_react_agent

load_dotenv()

from arize.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

class AgentFactory:
    def __init__(self):
        self.tool_map = {tool.name: tool for tool in AEON_TOOLS}
        
        arize_space_id = os.getenv("ARIZE_SPACE_ID")
        arize_api_key = os.getenv("ARIZE_API_KEY")
        
        if arize_space_id and arize_api_key:
            tracer_provider = register(
                space_id=arize_space_id,
                api_key=arize_api_key,
                project_name="aeon-wealth-factory"
            )
            LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
            print("👁️  Arize Telemetry Active: Tracing LLM calls, Tools, and PII Guardrails.")
        else:
            print("⚠️  Arize keys not found in .env. Telemetry disabled.")

        # 🛑 FIX: Build a heavy-duty AWS client with a 5-minute timeout
        self.bedrock_config = Config(
            region_name="us-east-1",
            read_timeout=300,        # Give Claude 5 full minutes to think!
            connect_timeout=120,
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        self.bedrock_client = boto3.client("bedrock-runtime", config=self.bedrock_config)

    def build_node(self, config: AgentConfig):
        # 🛑 FIX: Pass the heavy-duty client into LangChain
        llm = ChatBedrock(
            client=self.bedrock_client,
            model_id=config.model_id,
            max_tokens=4096,
            model_kwargs={"temperature": config.temperature}
        )

        agent_tools = [self.tool_map[t_name] for t_name in config.authorized_tools if t_name in self.tool_map]
        
        strict_persona = config.persona + "\n\nCRITICAL MAP-REDUCE INSTRUCTION: You are part of a parallel team. ONLY perform the specific task that relates to your domain. Do NOT attempt to answer the entire user prompt or synthesize the final response. Just output your raw findings clearly so the synthesis agent can combine them later."
        
        worker_agent = create_react_agent(
            model=llm,
            tools=agent_tools,
            prompt=strict_persona
        )

        def node_logic(state: dict):
            input_messages = list(state.get("messages", []))
            
            if input_messages and getattr(input_messages[-1], "type", None) in ["ai", "tool"]:
                nudge = f"Supervisor routing to {config.name}. Please execute your specific task based on the context above."
                input_messages.append(HumanMessage(content=nudge))
            
            result = worker_agent.invoke({"messages": input_messages})
            new_messages = result["messages"][len(input_messages):]
            
            return {"messages": new_messages, "current_agent": [config.name]} 

        return node_logic