from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List, Dict, Any
from db.database import get_db
from db.models import ProductCatalog, Review, Customer
import schemas
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/product-reviews",
    tags=["product-reviews"]
)

@router.get("/")
def test_endpoint():
    return {"message": "Product review routes are working!"}

@router.get("/metrics")
def get_review_metrics(
    brand: str = Query(None, description="Brand name to filter data"),
    product_name: str = None, 
    db: Session = Depends(get_db)
):
    """Get overall product review metrics"""
    logger.info("Processing /metrics endpoint request")
    try:
        query = db.query(Review).join(ProductCatalog)
        if product_name:
            query = query.filter(ProductCatalog.product_name == product_name)
        if brand:
            query = query.filter(ProductCatalog.brand == brand)

        total_reviews = query.count()
        positive_reviews = query.filter(Review.sentiment_score >= 0.5).count()
        negative_reviews = total_reviews - positive_reviews
        total_products = db.query(Review.product_id).distinct().count()

        response = {
            "totalProducts": total_products,
            "totalReviews": total_reviews,
            "positiveCount": positive_reviews,
            "negativeCount": negative_reviews
        }
        logger.info(f"Returning metrics response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in /metrics endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentiment-distribution")
def get_sentiment_distribution(
    brand: str = Query(None, description="Brand name to filter data"),
    product_name: str = None, 
    db: Session = Depends(get_db)
):
    """Get sentiment distribution data"""
    logger.info("Processing /sentiment-distribution endpoint request")
    try:
        query = db.query(Review).join(ProductCatalog)
        if product_name:
            query = query.filter(ProductCatalog.product_name == product_name)
        if brand:
            query = query.filter(ProductCatalog.brand == brand)

        total = query.count()
        positive = query.filter(Review.sentiment_score >= 0.5).count()
        negative = total - positive

        response = {
            "labels": ["Positive", "Negative"],
            "datasets": [{
                "data": [positive, negative],
                "backgroundColor": ['#00897b', '#f44336']
            }]
        }
        logger.info(f"Returning sentiment distribution response")
        return response
    except Exception as e:
        logger.error(f"Error in /sentiment-distribution endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aspect-sentiment")
def get_aspect_sentiment(
    brand: str = Query(None, description="Brand name to filter data"),
    product_name: str = None, 
    db: Session = Depends(get_db)
):
    """Get sentiment scores for different aspects"""
    logger.info("Processing /aspect-sentiment endpoint request")
    try:
        aspects = ['Kenyamanan', 'Harga', 'Kualitas', 'Desain']
        query = db.query(Review).join(ProductCatalog)
        if product_name:
            query = query.filter(ProductCatalog.product_name == product_name)
        if brand:
            query = query.filter(ProductCatalog.brand == brand)

        # This is a simplified version. In reality, you'd need NLP to extract aspect-based sentiment
        positive_scores = [80, 65, 75, 70]  # Example data
        negative_scores = [20, 35, 25, 30]  # Example data

        response = {
            "labels": aspects,
            "datasets": [
                {
                    "label": "Positive",
                    "data": positive_scores,
                    "backgroundColor": '#00897b',
                    "stack": 'Stack 0',
                },
                {
                    "label": "Negative",
                    "data": negative_scores,
                    "backgroundColor": '#f44336',
                    "stack": 'Stack 0',
                }
            ]
        }
        logger.info("Returning aspect sentiment response")
        return response
    except Exception as e:
        logger.error(f"Error in /aspect-sentiment endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products")
def get_products(
    brand: str = Query(None, description="Brand name to filter data"),
    db: Session = Depends(get_db)):
    """Get list of all products"""
    logger.info("Processing /products endpoint request")
    try:
        products = db.query(Review.product_id, ProductCatalog.product_name
        ).join(
            ProductCatalog,
            Review.product_id == ProductCatalog.product_id
        ).group_by(
            Review.product_id, ProductCatalog.product_name
        ).order_by(desc(ProductCatalog.product_name)
        ).filter(ProductCatalog.brand == brand).all()
        
        logger.info(f"Found {len(products)} products")
        return [{"product_id": p[0], "product_name": p[1]} for p in products]
    except Exception as e:
        logger.error(f"Error in /products endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
#products review sentiment
@router.get("/products-review-sentiment/{product_id}")
def get_products_review_sentiment(
    product_id: int, 
    brand: str = Query(None, description="Brand name to filter data"),
    db: Session = Depends(get_db)
):
    """get review sentiments based on product id"""
    logger.info("Processing /products-review-sentiment endpoint request")
    try:
        reviews = db.query(Review).filter(Review.product_id == product_id).all()
        
        logger.info(f"Found {len(reviews)} reviews for product_id {product_id}")
        
        # Mapping from database aspect names to frontend display names
        aspects = {
            "design": {"positive": 0, "negative": 0},
            "comfort": {"positive": 0, "negative": 0},
            "quality": {"positive": 0, "negative": 0},
            "durability": {"positive": 0, "negative": 0}
        }
        
        for review in reviews:
            if review.aspect_sentiments:
                # Parse JSON string to dict if needed
                aspect_scores = review.aspect_sentiments
                if isinstance(aspect_scores, str):
                    aspect_scores = json.loads(aspect_scores)
                
                logger.info(f"Processing aspect_sentiments: {aspect_scores}")
                
                # Map the database aspect names to frontend names and count sentiments
                for db_aspect, score in aspect_scores.items():
                    if float(score) >= 5:
                        aspects[db_aspect]["positive"] += 1
                    else:
                        aspects[db_aspect]["negative"] += 1
        
        result = {}
        for aspect, counts in aspects.items():
            total = counts["positive"] + counts["negative"]
            if total > 0:
                pos_percent = round((counts["positive"] / total) * 100)
                neg_percent = 100 - pos_percent
            else:
                pos_percent = 0
                neg_percent = 0
                
            result[aspect] = {
                "positive": pos_percent,
                "negative": neg_percent
            }
        
        logger.info(f"Final result: {result}")    
        return result
    except Exception as e:
        logger.error(f"Error in /products-review-sentiment endpoint: {str(e)}")
        logger.exception(e)  # This will log the full stack trace
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/filter-categories")
def get_filter_categories():
    """Get available filter categories"""
    return ['Jenis Bahan', 'Material Sol', 'Asal Produk', 'Target Gender']
    
#get review sentiment by upper material
@router.get("/review-sentiment-by-upper-material")
def get_review_sentiment_by_upper_material(
    brand: str = Query(None, description="Brand name to filter data"),
    db: Session = Depends(get_db)
):
    """Get review sentiment by upper material for each aspect"""
    logger.info("Processing /review-sentiment-by-upper-material endpoint request")
    try:
        # Get all reviews with their product's upper material
        reviews = db.query(
            Review, 
            ProductCatalog.upper_material
        ).join(
            ProductCatalog,
            Review.product_id == ProductCatalog.product_id
        ).all()
        
        upper_materials = db.query(ProductCatalog.upper_material).distinct().all()
        upper_materials = [um[0] for um in upper_materials]

        # Initialize the data structure
        results = {
            'Kenyamanan': {},
            'Kualitas': {},
            'Durabilitas': {},
            'Desain': {}
        }
        
        # Initialize counters for each material under each aspect
        for aspect in results:
            for material in upper_materials:
                results[aspect][material] = {'positive': 0, 'negative': 0}

        # Map the aspect names
        aspect_mapping = {
            'comfort': 'Kenyamanan',
            'quality': 'Kualitas',
            'durability': 'Durabilitas',
            'design': 'Desain'
        }

        # Process each review
        for review, upper_material in reviews:
            if review.aspect_sentiments:
                aspect_scores = review.aspect_sentiments
                if isinstance(aspect_scores, str):
                    aspect_scores = json.loads(aspect_scores)

                for db_aspect, score in aspect_scores.items():
                    if db_aspect in aspect_mapping:
                        frontend_aspect = aspect_mapping[db_aspect]
                        if float(score) >= 5:  # Score range is 1-10
                            results[frontend_aspect][upper_material]['positive'] += 1
                        else:
                            results[frontend_aspect][upper_material]['negative'] += 1

        # Calculate percentages
        response = {}
        for aspect, materials in results.items():
            response[aspect] = {}
            for material, counts in materials.items():
                total = counts['positive'] + counts['negative']
                if total > 0:
                    pos_percent = round((counts['positive'] / total) * 100)
                    neg_percent = 100 - pos_percent
                else:
                    pos_percent = 0
                    neg_percent = 0
                response[aspect][material] = {
                    'positive': pos_percent,
                    'negative': neg_percent
                }

        logger.info(f"Calculated sentiment percentages by aspect and upper material")
        return response
    except Exception as e:
        logger.error(f"Error in /review-sentiment-by-upper-material endpoint: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

#get review sentiment by sole material
@router.get("/review-sentiment-by-sole-material")
def get_review_sentiment_by_sole_material(
    brand: str = Query(None, description="Brand name to filter data"),
    db: Session = Depends(get_db)
):
    """Get review sentiment by sole material for each aspect"""
    logger.info("Processing /review-sentiment-by-sole-material endpoint request")
    try:
        # Get all reviews with their product's sole material
        reviews = db.query(
            Review, 
            ProductCatalog.sole_material
        ).join(
            ProductCatalog,
            Review.product_id == ProductCatalog.product_id
        ).all()
        
        sole_materials = db.query(ProductCatalog.sole_material).distinct().all()
        sole_materials = [sm[0] for sm in sole_materials]

        # Initialize the data structure
        results = {
            'Kenyamanan': {},
            'Kualitas': {},
            'Durabilitas': {},
            'Desain': {}
        }
        
        # Initialize counters for each material under each aspect
        for aspect in results:
            for material in sole_materials:
                results[aspect][material] = {'positive': 0, 'negative': 0}

        # Map the aspect names
        aspect_mapping = {
            'comfort': 'Kenyamanan',
            'quality': 'Kualitas',
            'durability': 'Durabilitas',
            'design': 'Desain'
        }

        # Process each review
        for review, sole_material in reviews:
            if review.aspect_sentiments:
                aspect_scores = review.aspect_sentiments
                if isinstance(aspect_scores, str):
                    aspect_scores = json.loads(aspect_scores)

                for db_aspect, score in aspect_scores.items():
                    if db_aspect in aspect_mapping:
                        frontend_aspect = aspect_mapping[db_aspect]
                        if float(score) >= 5:
                            results[frontend_aspect][sole_material]['positive'] += 1
                        else:
                            results[frontend_aspect][sole_material]['negative'] += 1

        # Calculate percentages
        response = {}
        for aspect, materials in results.items():
            response[aspect] = {}
            for material, counts in materials.items():
                total = counts['positive'] + counts['negative']
                if total > 0:
                    pos_percent = round((counts['positive'] / total) * 100)
                    neg_percent = 100 - pos_percent
                else:
                    pos_percent = 0
                    neg_percent = 0
                response[aspect][material] = {
                    'positive': pos_percent,
                    'negative': neg_percent
                }

        logger.info(f"Calculated sentiment percentages by aspect and sole material")
        return response
    except Exception as e:
        logger.error(f"Error in /review-sentiment-by-sole-material endpoint: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

#get review sentiment by origin
@router.get("/review-sentiment-by-origin")
def get_review_sentiment_by_origin(
    brand: str = Query(None, description="Brand name to filter data"),
    db: Session = Depends(get_db)
):
    """Get review sentiment by origin for each aspect"""
    logger.info("Processing /review-sentiment-by-origin endpoint request")
    try:
        # Get all reviews with their product's origin
        reviews = db.query(
            Review, 
            ProductCatalog.origin
        ).join(
            ProductCatalog,
            Review.product_id == ProductCatalog.product_id
        ).all()
        
        origins = db.query(ProductCatalog.origin).distinct().all()
        origins = [o[0] for o in origins]

        # Initialize the data structure
        results = {
            'Kenyamanan': {},
            'Kualitas': {},
            'Durabilitas': {},
            'Desain': {}
        }
        
        # Initialize counters for each origin under each aspect
        for aspect in results:
            for origin in origins:
                results[aspect][origin] = {'positive': 0, 'negative': 0}

        # Map the aspect names
        aspect_mapping = {
            'comfort': 'Kenyamanan',
            'quality': 'Kualitas',
            'durability': 'Durabilitas',
            'design': 'Desain'
        }

        # Process each review
        for review, origin in reviews:
            if review.aspect_sentiments:
                aspect_scores = review.aspect_sentiments
                if isinstance(aspect_scores, str):
                    aspect_scores = json.loads(aspect_scores)

                for db_aspect, score in aspect_scores.items():
                    if db_aspect in aspect_mapping:
                        frontend_aspect = aspect_mapping[db_aspect]
                        if float(score) >= 5:
                            results[frontend_aspect][origin]['positive'] += 1
                        else:
                            results[frontend_aspect][origin]['negative'] += 1

        # Calculate percentages
        response = {}
        for aspect, origins in results.items():
            response[aspect] = {}
            for origin, counts in origins.items():
                total = counts['positive'] + counts['negative']
                if total > 0:
                    pos_percent = round((counts['positive'] / total) * 100)
                    neg_percent = 100 - pos_percent
                else:
                    pos_percent = 0
                    neg_percent = 0
                response[aspect][origin] = {
                    'positive': pos_percent,
                    'negative': neg_percent
                }

        logger.info(f"Calculated sentiment percentages by aspect and origin")
        return response
    except Exception as e:
        logger.error(f"Error in /review-sentiment-by-origin endpoint: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

#get review sentiment by gender orientation
@router.get("/review-sentiment-by-gender")
def get_review_sentiment_by_gender(
    brand: str = Query(None, description="Brand name to filter data"),
    db: Session = Depends(get_db)
):
    """Get review sentiment by gender orientation for each aspect"""
    logger.info("Processing /review-sentiment-by-gender endpoint request")
    try:
        # Get all reviews with their product's gender orientation
        reviews = db.query(
            Review, 
            ProductCatalog.gender_orientation
        ).join(
            ProductCatalog,
            Review.product_id == ProductCatalog.product_id
        ).all()
        
        genders = db.query(ProductCatalog.gender_orientation).distinct().all()
        genders = [g[0] for g in genders]

        # Initialize the data structure
        results = {
            'Kenyamanan': {},
            'Kualitas': {},
            'Durabilitas': {},
            'Desain': {}
        }
        
        # Initialize counters for each gender under each aspect
        for aspect in results:
            for gender in genders:
                results[aspect][gender] = {'positive': 0, 'negative': 0}

        # Map the aspect names
        aspect_mapping = {
            'comfort': 'Kenyamanan',
            'quality': 'Kualitas',
            'durability': 'Durabilitas',
            'design': 'Desain'
        }

        # Process each review
        for review, gender in reviews:
            if review.aspect_sentiments:
                aspect_scores = review.aspect_sentiments
                if isinstance(aspect_scores, str):
                    aspect_scores = json.loads(aspect_scores)

                for db_aspect, score in aspect_scores.items():
                    if db_aspect in aspect_mapping:
                        frontend_aspect = aspect_mapping[db_aspect]
                        if float(score) >= 5:
                            results[frontend_aspect][gender]['positive'] += 1
                        else:
                            results[frontend_aspect][gender]['negative'] += 1

        # Calculate percentages
        response = {}
        for aspect, genders in results.items():
            response[aspect] = {}
            for gender, counts in genders.items():
                total = counts['positive'] + counts['negative']
                if total > 0:
                    pos_percent = round((counts['positive'] / total) * 100)
                    neg_percent = 100 - pos_percent
                else:
                    pos_percent = 0
                    neg_percent = 0
                response[aspect][gender] = {
                    'positive': pos_percent,
                    'negative': neg_percent
                }

        logger.info(f"Calculated sentiment percentages by aspect and gender orientation")
        return response
    except Exception as e:
        logger.error(f"Error in /review-sentiment-by-gender endpoint: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

#get top 10 positive and negative keywords from review
@router.get("/top-keywords")
def get_top_keywords(
    brand: str = Query(None, description="Brand name to filter data"),
    db: Session = Depends(get_db)
):
    """Get top 10 positive and negative keywords from review texts"""
    logger.info("Processing /top-keywords endpoint request")
    try:
        query = db.query(Review.keyword_tags).join(ProductCatalog)
        if brand:
            query = query.filter(ProductCatalog.brand == brand)

        # Collect all keywords and their frequencies
        keyword_freq = {}
        for review in query.all():
            if review.keyword_tags:
                for tag in review.keyword_tags:
                    keyword_freq[tag] = keyword_freq.get(tag, 0) + 1

        # Get top 10 positive and negative keywords
        top_positive = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        top_negative = sorted(keyword_freq.items(), key=lambda x: x[1])[:10]

        return {"positive": top_positive, "negative": top_negative}
    except Exception as e:
        logger.error(f"Error in /top-keywords endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))