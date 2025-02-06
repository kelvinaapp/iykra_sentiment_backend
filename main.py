from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import db.models
from db.database import SessionLocal, engine, get_db
import uvicorn
from routes_social_media import router as social_media_router
from routes_social_media_sentiment import router as sentiment_router
from routes_product_review_sentiment import router as product_review_router
from routes_sales import router as sales_router
from routes_ai_chatbot import router as ai_router
import logging
from tools.faiss_vectordb import load_vector_db

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize vector database
vector_store = None
try:
    logger.info("Loading vector database...")
    vector_store = load_vector_db("vector_db")
    logger.info("Vector database loaded successfully")
except Exception as e:
    logger.error(f"Failed to load vector database: {str(e)}")
    raise e

app = FastAPI(
    title="Shoe Brand Sentiment Analysis API",
    description="API for analyzing sentiment data of various shoe brands",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(social_media_router)
app.include_router(sentiment_router)
app.include_router(product_review_router)
app.include_router(sales_router)
app.include_router(ai_router)

# Make vector_store available to routes
app.state.vector_store = vector_store

# Root endpoint
@app.get("/api")
def read_root():
    return {"message": "Welcome to the Shoe Brand Sentiment Analysis API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
