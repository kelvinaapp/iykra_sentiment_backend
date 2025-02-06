from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from database import SessionLocal, engine, get_db
import uvicorn
from social_media_routes import router as social_media_router
from social_media_sentiment_routes import router as sentiment_router
from product_review_sentiment import router as product_review_router
from ai_generation import router as ai_router, generate_dashboard_summary
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

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
app.include_router(ai_router)

# Root endpoint
@app.get("/api")
def read_root():
    return {"message": "Welcome to the Shoe Brand Sentiment Analysis API"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
