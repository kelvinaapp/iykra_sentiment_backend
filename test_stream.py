import httpx
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def stream_data():
    try:
        timeout = httpx.Timeout(30.0)  # 5 minutes timeout
        logger.info("Starting request to AI chatbot...")
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info("Sending POST request...")
            async with client.stream(
                "POST", 
                "http://127.0.0.1:8000/api/ai/chat", 
                json={
                    "message": "bandingkan trend sentimen kelima brand pada bulan per minggunya pada desember 2024. tampilkan dalam tabel"
                }
            ) as response:
                logger.info(f"Response status: {response.status_code}")
                async for chunk in response.aiter_text():
                    print(chunk)
                    
    except httpx.ReadTimeout as e:
        logger.error(f"Request timed out after {timeout.read} seconds: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"An error occurred while making the request: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(stream_data())