from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, text
from datetime import datetime, timedelta
from typing import List, Dict, Any
<<<<<<< HEAD:product_review_sentiment.py
from database import get_db
from models import ProductCatalog, Review, Customer
import schemas
=======
from db.database import get_db
from db.models import ProductCatalog, ReviewedProduct, CustomerDemographics
>>>>>>> recover-commit:routes_product_review_sentiment.py
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
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get overall product review metrics"""
    logger.info("Processing /metrics endpoint request")
    try:
        query = db.query(ReviewedProduct).join(ProductCatalog)
        
        filters = []
        if product_name:
            filters.append(ProductCatalog.product_name == product_name)
        if brand:
            filters.append(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        query = query.filter(*filters)

        total_reviews = query.count()
        positive_reviews = query.filter(ReviewedProduct.sentiment_score >= 0.5).count()
        negative_reviews = total_reviews - positive_reviews
        
        # Calculate average rating
        avg_rating = db.query(func.avg(ReviewedProduct.rating)).filter(*filters).scalar()
        avg_rating = float(avg_rating) if avg_rating is not None else 0

        response = {
            "averageRating": round(avg_rating, 1),
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
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get sentiment distribution data"""
    logger.info("Processing /sentiment-distribution endpoint request")
    try:
        query = db.query(ReviewedProduct).join(ProductCatalog)
        
        filters = []
        if product_name:
            filters.append(ProductCatalog.product_name == product_name)
        if brand:
            filters.append(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        query = query.filter(*filters)

        total = query.count()
        positive = query.filter(ReviewedProduct.sentiment_score >= 0.5).count()
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
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get sentiment scores for different aspects"""
    logger.info("Processing /aspect-sentiment endpoint request")
    try:
        # Map the aspect names
        aspect_mapping = {
            'comfort': 'Kenyamanan',
            'quality': 'Kualitas',
            'durability': 'Durabilitas',
            'design': 'Desain'
        }
        
        query = db.query(ReviewedProduct).join(ProductCatalog)
        
        filters = []
        if product_name:
            filters.append(ProductCatalog.product_name == product_name)
        if brand:
            filters.append(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        query = query.filter(*filters)

        # Initialize counters for each aspect
        aspect_counts = {aspect: {'positive': 0, 'negative': 0} for aspect in aspect_mapping.values()}

        # Process each review
        for review in query.all():
            if review.aspect_sentiments:
                aspect_scores = review.aspect_sentiments
                if isinstance(aspect_scores, str):
                    aspect_scores = json.loads(aspect_scores)

                for db_aspect, score in aspect_scores.items():
                    if db_aspect in aspect_mapping:
                        frontend_aspect = aspect_mapping[db_aspect]
                        if float(score) >= 5:  # Score range is 1-10
                            aspect_counts[frontend_aspect]['positive'] += 1
                        else:
                            aspect_counts[frontend_aspect]['negative'] += 1

        # Calculate percentages and prepare response
        aspects = list(aspect_mapping.values())
        positive_scores = []
        negative_scores = []

        for aspect in aspects:
            total = aspect_counts[aspect]['positive'] + aspect_counts[aspect]['negative']
            if total > 0:
                pos_percent = round((aspect_counts[aspect]['positive'] / total) * 100)
                neg_percent = 100 - pos_percent
            else:
                pos_percent = 0
                neg_percent = 0
            positive_scores.append(pos_percent)
            negative_scores.append(neg_percent)

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
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)):
    """Get list of all products"""
    logger.info("Processing /products endpoint request")
    try:
        query = db.query(ReviewedProduct.product_id, ProductCatalog.product_name
        ).join(
            ProductCatalog,
            ReviewedProduct.product_id == ProductCatalog.product_id
        ).group_by(
            ReviewedProduct.product_id, ProductCatalog.product_name
        ).order_by(desc(ProductCatalog.product_name)
        )
        
        filters = []
        if brand:
            filters.append(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        query = query.filter(*filters)

        products = query.all()
        
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
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """get review sentiments based on product id"""
    logger.info("Processing /products-review-sentiment endpoint request")
    try:
        query = db.query(ReviewedProduct).filter(ReviewedProduct.product_id == product_id)
        
        filters = []
        if brand:
            query = query.join(ProductCatalog).filter(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        query = query.filter(*filters)

        reviews = query.all()
        
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
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get review sentiment by upper material for each aspect"""
    logger.info("Processing /review-sentiment-by-upper-material endpoint request")
    try:
        # Get all reviews with their product's upper material
        query = db.query(
            ReviewedProduct, 
            ProductCatalog.upper_material
        ).join(
            ProductCatalog,
            ReviewedProduct.product_id == ProductCatalog.product_id
        )
        
        # Build all filters first
        filters = []
        if brand:
            filters.append(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        # Apply all filters at once
        query = query.filter(*filters)

        # Get distinct upper materials for this brand and date range
        upper_materials_query = db.query(ProductCatalog.upper_material).distinct()
        if brand:
            upper_materials_query = upper_materials_query.filter(ProductCatalog.brand == brand)
        upper_materials = [um[0] for um in upper_materials_query.all() if um[0] is not None]

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
        for review, upper_material in query.all():
            if review.aspect_sentiments and upper_material:
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
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get review sentiment by sole material for each aspect"""
    logger.info("Processing /review-sentiment-by-sole-material endpoint request")
    try:
        # Get all reviews with their product's sole material
        query = db.query(
            ReviewedProduct, 
            ProductCatalog.sole_material
        ).join(
            ProductCatalog,
            ReviewedProduct.product_id == ProductCatalog.product_id
        )
        
        # Build all filters first
        filters = []
        if brand:
            filters.append(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        # Apply all filters at once
        query = query.filter(*filters)

        # Get distinct sole materials for this brand and date range
        sole_materials_query = db.query(ProductCatalog.sole_material).distinct()
        if brand:
            sole_materials_query = sole_materials_query.filter(ProductCatalog.brand == brand)
        sole_materials = [sm[0] for sm in sole_materials_query.all() if sm[0] is not None]

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
        for review, sole_material in query.all():
            if review.aspect_sentiments and sole_material:
                aspect_scores = review.aspect_sentiments
                if isinstance(aspect_scores, str):
                    aspect_scores = json.loads(aspect_scores)

                for db_aspect, score in aspect_scores.items():
                    if db_aspect in aspect_mapping:
                        frontend_aspect = aspect_mapping[db_aspect]
                        if float(score) >= 5:  # Score range is 1-10
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
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get review sentiment by origin for each aspect"""
    logger.info("Processing /review-sentiment-by-origin endpoint request")
    try:
        # Get all reviews with their product's origin
        query = db.query(
            ReviewedProduct, 
            ProductCatalog.origin
        ).join(
            ProductCatalog,
            ReviewedProduct.product_id == ProductCatalog.product_id
        )
        
        # Build all filters first
        filters = []
        if brand:
            filters.append(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        # Apply all filters at once
        query = query.filter(*filters)

        # Get distinct origins for this brand and date range
        origins_query = db.query(ProductCatalog.origin).distinct()
        if brand:
            origins_query = origins_query.filter(ProductCatalog.brand == brand)
        origins = [o[0] for o in origins_query.all() if o[0] is not None]

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
        for review, origin in query.all():
            if review.aspect_sentiments and origin:
                aspect_scores = review.aspect_sentiments
                if isinstance(aspect_scores, str):
                    aspect_scores = json.loads(aspect_scores)

                for db_aspect, score in aspect_scores.items():
                    if db_aspect in aspect_mapping:
                        frontend_aspect = aspect_mapping[db_aspect]
                        if float(score) >= 5:  # Score range is 1-10
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
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get review sentiment by gender orientation for each aspect"""
    logger.info("Processing /review-sentiment-by-gender endpoint request")
    try:
        # Get all reviews with their product's gender orientation
        query = db.query(
            ReviewedProduct, 
            ProductCatalog.gender_orientation
        ).join(
            ProductCatalog,
            ReviewedProduct.product_id == ProductCatalog.product_id
        )
        
        # Build all filters first
        filters = []
        if brand:
            filters.append(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        # Apply all filters at once
        query = query.filter(*filters)

        # Get distinct gender orientations for this brand and date range
        genders_query = db.query(ProductCatalog.gender_orientation).distinct()
        if brand:
            genders_query = genders_query.filter(ProductCatalog.brand == brand)
        genders = [g[0] for g in genders_query.all() if g[0] is not None]

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
        for review, gender in query.all():
            if review.aspect_sentiments and gender:
                aspect_scores = review.aspect_sentiments
                if isinstance(aspect_scores, str):
                    aspect_scores = json.loads(aspect_scores)

                for db_aspect, score in aspect_scores.items():
                    if db_aspect in aspect_mapping:
                        frontend_aspect = aspect_mapping[db_aspect]
                        if float(score) >= 5:  # Score range is 1-10
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

        logger.info(f"Calculated sentiment percentages by aspect and gender")
        return response
    except Exception as e:
        logger.error(f"Error in /review-sentiment-by-gender endpoint: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

#get top 10 positive and negative keywords from review
@router.get("/top-keywords")
def get_top_keywords(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get top 10 positive and negative keywords from review texts"""
    logger.info("Processing /top-keywords endpoint request")
    try:
        query = db.query(ReviewedProduct.keyword_tags).join(ProductCatalog)
        
        filters = []
        if brand:
            query = query.filter(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        query = query.filter(*filters)

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

@router.get("/emotion-intensity")
def get_emotion_intensity(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get distribution of emotion intensity in reviews"""
    logger.info("Processing /emotion-intensity endpoint request")
    try:
        query = db.query(ReviewedProduct).join(ProductCatalog)
        
        filters = []
        if brand:
            filters.append(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        query = query.filter(*filters)
        
        # Get total count for percentage calculation
        total_reviews = query.count()
        if total_reviews == 0:
            return {
                "veryLow": 0,
                "low": 0,
                "moderate": 0,
                "high": 0,
                "veryHigh": 0
            }
            
        # Count reviews in each emotion intensity range
        very_low = query.filter(ReviewedProduct.emotion_score < 0.2).count()
        low = query.filter(ReviewedProduct.emotion_score.between(0.2, 0.4)).count()
        moderate = query.filter(ReviewedProduct.emotion_score.between(0.4, 0.6)).count()
        high = query.filter(ReviewedProduct.emotion_score.between(0.6, 0.8)).count()
        very_high = query.filter(ReviewedProduct.emotion_score >= 0.8).count()
        
        # Calculate percentages
        response = {
            "veryLow": round((very_low / total_reviews) * 100),
            "low": round((low / total_reviews) * 100),
            "moderate": round((moderate / total_reviews) * 100),
            "high": round((high / total_reviews) * 100),
            "veryHigh": round((very_high / total_reviews) * 100)
        }
        
        logger.info(f"Returning emotion intensity distribution: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in /emotion-intensity endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-topics")
def get_top_topics(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get top review topics based on keyword tags"""
    logger.info("Processing /top-topics endpoint request")
    try:
        query = db.query(
            func.unnest(ReviewedProduct.keyword_tags).label('topic'),
            func.count().label('count')
        ).join(ProductCatalog)
        
        filters = []
        if brand:
            filters.append(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        query = query.filter(*filters)
        
        # Group by topic and order by count
        results = query.group_by('topic').order_by(text('count DESC')).limit(10).all()
        
        response = [
            {"topic": topic, "count": count}
            for topic, count in results
            if topic  # Filter out None values
        ]
        
        logger.info(f"Returning top topics: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in /top-topics endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rating-sentiment-correlation")
def get_rating_sentiment_correlation(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get correlation between ratings and sentiment scores"""
    logger.info("Processing /rating-sentiment-correlation endpoint request")
    try:
        query = db.query(
            ReviewedProduct.rating,
            func.avg(ReviewedProduct.sentiment_score).label('avg_sentiment'),
            func.count().label('count')
        ).join(ProductCatalog)
        
        filters = []
        if brand:
            filters.append(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        query = query.filter(*filters)
        
        # Group by rating
        results = query.group_by(ReviewedProduct.rating).order_by(ReviewedProduct.rating).all()
        
        response = [
            {
                "rating": rating,
                "averageSentiment": float(avg_sentiment) if avg_sentiment else 0,
                "reviewCount": count
            }
            for rating, avg_sentiment, count in results
            if rating is not None
        ]
        
        logger.info(f"Returning rating-sentiment correlation: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in /rating-sentiment-correlation endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/helpful-reviews")
def get_helpful_reviews(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    limit: int = Query(5, description="Number of reviews to return"),
    db: Session = Depends(get_db)
):
    """Get most helpful reviews based on helpful votes"""
    logger.info("Processing /helpful-reviews endpoint request")
    try:
        query = db.query(
            ReviewedProduct.review_text,
            ReviewedProduct.rating,
            ReviewedProduct.helpful_votes,
            ReviewedProduct.sentiment_score,
            ProductCatalog.product_name
        ).join(ProductCatalog)
        
        filters = []
        if brand:
            filters.append(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        query = query.filter(*filters)
        
        # Order by helpful votes and limit results
        results = query.order_by(ReviewedProduct.helpful_votes.desc()).limit(limit).all()
        
        response = [
            {
                "review": review_text,
                "rating": rating,
                "helpfulVotes": helpful_votes,
                "sentimentScore": float(sentiment_score) if sentiment_score else 0,
                "productName": product_name
            }
            for review_text, rating, helpful_votes, sentiment_score, product_name in results
            if review_text  # Filter out None values
        ]
        
        logger.info(f"Returning helpful reviews: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in /helpful-reviews endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trend")
def get_sentiment_rating_trend(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get daily trend of average sentiment and rating"""
    logger.info("Processing /trend endpoint request")
    try:
        query = db.query(
            ReviewedProduct.review_date,
            func.avg(ReviewedProduct.sentiment_score).label('avg_sentiment'),
            func.avg(ReviewedProduct.rating).label('avg_rating'),
            func.count().label('review_count')
        ).join(ProductCatalog)
        
        filters = []
        if brand:
            filters.append(ProductCatalog.brand == brand)
        if startDate and endDate:
            filters.append(ReviewedProduct.review_date.between(startDate, endDate))
            
        query = query.filter(*filters)
        
        # Group by date and get daily averages
        results = query.group_by(ReviewedProduct.review_date)\
                      .order_by(ReviewedProduct.review_date)\
                      .all()
        
        response = [
            {
                "date": date.strftime("%Y-%m-%d"),
                "averageSentiment": float(avg_sentiment) if avg_sentiment else 0,
                "averageRating": float(avg_rating) if avg_rating else 0,
                "reviewCount": count
            }
            for date, avg_sentiment, avg_rating, count in results
        ]
        
        logger.info(f"Returning trend data with {len(response)} data points")
        return response
    except Exception as e:
        logger.error(f"Error in /trend endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))