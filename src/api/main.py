# src/api/main.py
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import asyncio

# Import our compiled LangGraph application
from src.agents.graph import aeon_app
from langchain_core.messages import HumanMessage
from langgraph.types import Command

app = FastAPI(title="Aeon Wealth Agent Factory API")

class ChatRequest(BaseModel):
    message: str
    thread_id: str
    # If the graph was paused for human input, the frontend will send true here
    is_clarification: bool = False 

async def event_generator(request: ChatRequest):
    """
    Generator function to stream LangGraph events to the frontend via SSE.
    """
    config = {"configurable": {"thread_id": request.thread_id}}
    
    try:
        # 1. Determine if this is a new message or a clarification for a paused graph
        if request.is_clarification:
            # Resume the graph using the human's answer
            stream = aeon_app.astream(Command(resume=request.message), config=config, stream_mode="values")
        else:
            # Start a new query
            inputs = {"messages": [HumanMessage(content=request.message)]}
            stream = aeon_app.astream(inputs, config=config, stream_mode="values")

        # 2. Iterate through the graph's execution steps
        async for event in stream:
            # Check if the graph paused for Human-in-the-Loop
            state = aeon_app.get_state(config)
            if state.next:
                clarification_prompt = event.get("routing_log", ["Please clarify."])[-1]
                yield f"data: {json.dumps({'type': 'interrupt', 'message': clarification_prompt})}\n\n"
                return # Stop the stream, wait for frontend to send a clarification request

            # Stream routing updates to the UI (e.g., "Checking Portfolio...")
            if "routing_log" in event and event["routing_log"]:
                latest_route = event["routing_log"][-1]
                yield f"data: {json.dumps({'type': 'routing', 'message': latest_route})}\n\n"

            # Stream the final AI message
            if "messages" in event and event["messages"]:
                last_msg = event["messages"][-1]
                if getattr(last_msg, "type", None) == "ai" and last_msg.content:
                    # Small sleep to ensure chunks flush properly
                    await asyncio.sleep(0.01)
                    yield f"data: {json.dumps({'type': 'token', 'content': last_msg.content})}\n\n"
                    
        # Signal completion
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    The main endpoint for the conversational UI. Returns a StreamingResponse.
    """
    return StreamingResponse(event_generator(request), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    # Run the API on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)