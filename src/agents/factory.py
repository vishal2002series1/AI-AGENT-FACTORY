# src/agents/factory.py
import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage  # <-- Added import
from src.agents.tools import AEON_TOOLS
from src.agents.config import AgentConfig
from langgraph.prebuilt import create_react_agent

# Load environment variables from .env file
load_dotenv()

# --- The Arize "GoPro" Setup ---
from arize.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

class AgentFactory:
    def __init__(self):
        """Initializes the factory and reads Arize keys directly from the environment."""
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

    def build_node(self, config: AgentConfig):
        """The Assembly Line: Builds a worker that automatically executes its tools."""
        llm = ChatBedrock(
            model_id=config.model_id,
            region_name="us-east-1",
            max_tokens=4096,
            model_kwargs={"temperature": config.temperature}
        )

        agent_tools = [self.tool_map[t_name] for t_name in config.authorized_tools if t_name in self.tool_map]
        
        worker_agent = create_react_agent(
            model=llm,
            tools=agent_tools,
            prompt=config.persona
        )

        def node_logic(state: dict):
            # 1. Grab the current conversation history
            input_messages = list(state.get("messages", []))
            
            # 🛑 AWS BEDROCK FIX: Anthropic Claude strictly requires the conversation history 
            # to end with a Human message. If the previous agent left an AI message, we inject a nudge.
            if input_messages and getattr(input_messages[-1], "type", None) in ["ai", "tool"]:
                nudge = f"Supervisor routing to {config.name}. Please execute your specific task based on the context above."
                input_messages.append(HumanMessage(content=nudge))
            
            # 2. Pass the padded clipboard to the worker agent
            result = worker_agent.invoke({"messages": input_messages})
            
            # 3. Extract ONLY the newly generated messages by slicing off the input history
            new_messages = result["messages"][len(input_messages):]
            
            # 4. Hand the new messages back to the Supervisor
            return {"messages": new_messages, "current_agent": config.name}

        return node_logic