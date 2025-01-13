from fastapi import APIRouter, Depends, HTTPException
import os
from dotenv import load_dotenv
from openai import OpenAI
from flask import jsonify
import logging
from pydantic import BaseModel
from typing import Dict, Any
import json
import httpx

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/ai",
    tags=["social-media"]
)

# Load environment variables
load_dotenv()

# Configure OpenAI
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    logger.error("OpenAI API key not found in environment variables")
else:
    logger.info("OpenAI API key loaded successfully")

# Initialize OpenAI client with custom httpx client
http_client = httpx.Client()
client = OpenAI(
    api_key=api_key,
    http_client=http_client
)

# Pydantic model for request validation
class DashboardSummaryRequest(BaseModel):
    dashboard_data: Dict[str, Any]
    brand: str

@router.post("/dashboard-summary")
async def get_dashboard_summary(request: DashboardSummaryRequest):
    """
    Generate an AI summary for dashboard data
    """
    try:
        logger.info(f"Received request for brand: {request.brand}")
        # logger.debug(f"Dashboard data: {json.dumps(request.dashboard_data, indent=2)}")
        
        result = generate_dashboard_summary(request.dashboard_data, request.brand)
        logger.info(f"Generated summary status: {result['status']}")
        
        if result["status"] == "error":
            logger.error(f"Error in generate_dashboard_summary: {result['message']}")
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except Exception as e:
        logger.error(f"Error in get_dashboard_summary endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def generate_dashboard_summary(dashboard_data, brand):
    """
    Generate an AI summary of the entire dashboard data
    """
    try:
        logger.info(f"Generating summary for brand: {brand}")
        
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
        logger.info("Calling OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a business analytics expert who provides clear, actionable insights from dashboard data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        logger.info("Received response from OpenAI API")

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
