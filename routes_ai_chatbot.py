from fastapi import APIRouter, Depends, HTTPException, Request
import os
from dotenv import load_dotenv
from openai import OpenAI
import logging
from pydantic import BaseModel
from typing import Dict, Any
import json
import httpx
from tools.langchain_rag import LangChainRAG
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("openai").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

router = APIRouter(
    prefix="/api/ai",
    tags=["social-media"]
)

# Load environment variables
load_dotenv()

# Configure OpenAI
api_key = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client with custom httpx client
http_client = httpx.Client()
client = OpenAI(
    api_key=api_key,
    http_client=http_client
)

# Initialize LangChainRAG instance when module is imported
rag_agent = None

def init_rag_agent(request: Request = None):
    global rag_agent
    try:
        vector_store = request.app.state.vector_store if request else None
        rag_agent = LangChainRAG(vector_store=vector_store)
        # logger.info("LangChainRAG agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LangChainRAG agent: {str(e)}")
        raise e

# Pydantic model for request validation
class DashboardSummaryRequest(BaseModel):
    dashboard_data: Dict[str, Any]
    brand: str

# Pydantic model for chat request
class ChatRequest(BaseModel):
    message: str

@router.post("/dashboard-summary")
async def get_dashboard_summary(request: DashboardSummaryRequest):
    """
    Generate an AI summary for dashboard data
    """
    try:
        # logger.info(f"Received request for brand: {request.brand}")
        # logger.debug(f"Dashboard data: {json.dumps(request.dashboard_data, indent=2)}")
        
        result = generate_dashboard_summary(request.dashboard_data, request.brand)
        # logger.info(f"Generated summary status: {result['status']}")
        
        if result["status"] == "error":
            logger.error(f"Error in generate_dashboard_summary: {result['message']}")
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except Exception as e:
        logger.error(f"Error in get_dashboard_summary endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_with_agent(request: Request, chat_request: ChatRequest):
    """
    Chat with the AI agent using RAG (Retrieval Augmented Generation)
    """
    try:
        # Initialize agent if not already initialized
        if rag_agent is None:
            init_rag_agent(request)
            
        # logger.info(f"Received chat message: {chat_request.message}")
        
        async def event_generator():
            try:
                current_chunk = ""
                async for chunk in rag_agent.run_agent(chat_request.message):
                    if chunk:
                        try:
                            # Parse the chunk as JSON
                            chunk_data = json.loads(chunk)
                            if chunk_data.get("text"):
                                # Send the text chunk
                                yield f"data: {json.dumps(chunk_data)}\n\n"
                        except json.JSONDecodeError:
                            # If chunk is not JSON, send it as raw text
                            yield f"data: {json.dumps({'text': chunk})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Error in event_generator: {str(e)}")
                error_message = json.dumps({"error": str(e)})
                yield f"data: {error_message}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream;charset=utf-8",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Max-Age": "86400",
            }
        )
    except Exception as e:
        logger.error(f"Error in chat_with_agent endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/reset")
async def reset_agent(request: Request):
    """
    Reset the RAG agent by reinitializing it
    """
    try:
        # logger.info("Reinitializing RAG agent...")
        init_rag_agent(request)
        return {"status": "success", "message": "Agent reinitialized successfully"}
    except Exception as e:
        logger.error(f"Error reinitializing agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def generate_dashboard_summary(dashboard_data, brand):
    """
    Generate an AI summary of the entire dashboard data
    """
    try:
        # logger.info(f"Generating summary for brand: {brand}")
        
        # Prepare the prompt with dashboard data
        prompt = f"""Analyze this dashboard data for {brand} and provide a comprehensive business summary:

        Brand: {brand}
        Dashboard Data: {json.dumps(dashboard_data, indent=2)}

        Please provide:
        1. Key performance insights
        2. Actionable recommendations
        
        do not talk to much about the data. just provide the summary in the most easy way possible. 
        the summary should be easy to understand. use high level perspective like we talk to CEOs.
        do not use list, use numbering and paragraphs to explain the data. reposonse should be short and clear.
        """
        
        # logger.debug(f"Generated prompt: {prompt}")

        # Call OpenAI API
        # logger.info("Calling OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a business analytics expert who provides clear, actionable insights from dashboard data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        # logger.info("Received response from OpenAI API")

        # Extract the summary
        summary = response.choices[0].message.content
        logger.debug(f"Generated summary: {summary}")

        return {
            "status": "success",
            "summary": summary,
            "brand": brand
        }

    except Exception as e:
        logger.error(f"Error in generate_dashboard_summary: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }
