from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List, Dict
from datetime import datetime, timedelta
from  db.models import SentimentSocialMedia, SocialMedia
from db.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/social-media-sentiment",
    tags=["sentiment"]
)

@router.get("/")
def test_endpoint():
    return {"message": "Social media sentiment routes are working!"}

@router.get("/overview")
def get_sentiment_overview(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get overview metrics filtered by brand and date range"""
    try:
        # Base queries
        comments_query = db.query(SentimentSocialMedia)
        posts_query = db.query(SocialMedia)
        likes_query = db.query(func.sum(SentimentSocialMedia.total_likes))
        replies_query = db.query(func.sum(SentimentSocialMedia.total_replies))
        engagement_query = db.query(func.sum(SocialMedia.engagement_count))
        sentiment_query = db.query(SentimentSocialMedia)
        
        filters = []
        if brand:
            filters.append(SocialMedia.brand == brand)
        if startDate and endDate:
            filters.append(SocialMedia.post_date.between(startDate, endDate))

        # Apply filters
        comments_query = comments_query.join(
            SocialMedia,
            SocialMedia.social_media_post_id == SentimentSocialMedia.id_post
        ).filter(*filters)
        
        posts_query = posts_query.filter(*filters)
        
        likes_query = likes_query.join(
            SocialMedia,
            SocialMedia.social_media_post_id == SentimentSocialMedia.id_post
        ).filter(*filters)
        
        replies_query = replies_query.join(
            SocialMedia,
            SocialMedia.social_media_post_id == SentimentSocialMedia.id_post
        ).filter(*filters)
        
        engagement_query = engagement_query.filter(*filters)
        
        sentiment_query = sentiment_query.join(
            SocialMedia,
            SocialMedia.social_media_post_id == SentimentSocialMedia.id_post
        ).filter(*filters)
        
        # Get results
        total_comments = comments_query.count()
        total_posts = posts_query.count()
        total_likes = likes_query.scalar() or 0
        total_replies = replies_query.scalar() or 0
        total_engagement = engagement_query.scalar() or 0
        
        # Get sentiment distribution
        total_sentiments = total_comments
        positive_sentiments = sentiment_query.filter(
            SentimentSocialMedia.sentiment_score > 0.5
        ).count()
        
        return {
            "totalComments": total_comments,
            "totalPosts": total_posts,
            "totalEngagement": total_engagement + total_likes + total_replies,
            "sentimentDistribution": {
                "positive": round((positive_sentiments / total_sentiments) * 100 if total_sentiments > 0 else 0),
                "negative": round(((total_sentiments - positive_sentiments) / total_sentiments) * 100 if total_sentiments > 0 else 0)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platform-sentiment")
def get_platform_sentiment(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get sentiment distribution by platform filtered by brand and date range"""
    try:
        # Base query
        query = db.query(
            SocialMedia.platform,
            func.count(SentimentSocialMedia.id_post).label('total'),
            func.count(SentimentSocialMedia.id_post).filter(
                SentimentSocialMedia.sentiment_score > 0.5
            ).label('positive')
        ).join(
            SentimentSocialMedia,
            SocialMedia.social_media_post_id == SentimentSocialMedia.id_post
        )
        
        filters = []
        if brand:
            filters.append(SocialMedia.brand == brand)
        if startDate and endDate:
            filters.append(SocialMedia.post_date.between(startDate, endDate))

        # Apply filters
        query = query.filter(*filters)
        
        platform_sentiment = query.group_by(
            SocialMedia.platform
        ).all()
        
        result = {}
        for platform, total, positive in platform_sentiment:
            negative = total - positive
            result[platform] = {
                "positive": positive,
                "negative": negative
            }
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/time-series")
def get_sentiment_time_series(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get sentiment trends over time filtered by brand and date range"""
    try:
        # Convert string dates to datetime objects if provided, otherwise use default range
        if startDate and endDate:
            start_date = datetime.strptime(startDate, "%Y-%m-%d")
            end_date = datetime.strptime(endDate, "%Y-%m-%d")
        else:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=days)
        
        # Base query
        query = db.query(
            func.date(SocialMedia.post_date).label('date'),
            func.count(SentimentSocialMedia.id_post).label('total'),
            func.count(SentimentSocialMedia.id_post).filter(
                SentimentSocialMedia.sentiment_score > 0.5
            ).label('positive')
        ).join(
            SentimentSocialMedia,
            SocialMedia.social_media_post_id == SentimentSocialMedia.id_post
        )
        
        filters = []
        if brand:
            filters.append(SocialMedia.brand == brand)
        
        # Always add date filter using the determined date range
        filters.append(SocialMedia.post_date.between(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        ))

        # Apply filters
        query = query.filter(*filters)
        
        daily_sentiment = query.group_by(
            func.date(SocialMedia.post_date)
        ).order_by(
            func.date(SocialMedia.post_date)
        ).all()
        
        result = {
            "labels": [],
            "positive": [],
            "negative": []
        }
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")  
            result["labels"].append(date_str)
            
            day_data = next((data for data in daily_sentiment if data.date == current_date.date()), None)
            if day_data:
                total = day_data.total
                positive = day_data.positive
                result["positive"].append(round((positive / total) * 100))
                result["negative"].append(round(((total - positive) / total) * 100))
            else:
                result["positive"].append(0)
                result["negative"].append(0)
            
            current_date += timedelta(days=1)
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/keywords")
def get_sentiment_keywords(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get top keywords filtered by brand and date range"""
    try:
        # Base queries
        positive_query = db.query(
            func.regexp_split_to_table(SentimentSocialMedia.comment, ' ').label('word'),
            func.count('*').label('count')
        ).join(
            SocialMedia,
            SocialMedia.social_media_post_id == SentimentSocialMedia.id_post
        ).filter(
            SentimentSocialMedia.sentiment_score > 0.5
        )
        
        negative_query = db.query(
            func.regexp_split_to_table(SentimentSocialMedia.comment, ' ').label('word'),
            func.count('*').label('count')
        ).join(
            SocialMedia,
            SocialMedia.social_media_post_id == SentimentSocialMedia.id_post
        ).filter(
            SentimentSocialMedia.sentiment_score <= 0.5
        )
        
        filters = []
        if brand:
            filters.append(SocialMedia.brand == brand)
        if startDate and endDate:
            filters.append(SocialMedia.post_date.between(startDate, endDate))

        # Apply filters
        positive_query = positive_query.filter(*filters)
        negative_query = negative_query.filter(*filters)
        
        positive_keywords = positive_query.group_by(
            'word'
        ).order_by(
            func.count('*').desc()
        ).limit(10).all()

        negative_keywords = negative_query.group_by(
            'word'
        ).order_by(
            func.count('*').desc()
        ).limit(10).all()

        return {
            "positive": [{"text": word, "value": count} for word, count in positive_keywords],
            "negative": [{"text": word, "value": count} for word, count in negative_keywords]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending-hashtags")
def get_trending_hashtags(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get trending hashtags filtered by brand and date range"""
    try:
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=7)
        prev_start = start_date - timedelta(days=7)
        
        # Base queries
        current_query = db.query(
            func.unnest(SocialMedia.hashtags).label('hashtag'),
            func.count('*').label('count')
        ).filter(
            SocialMedia.post_date > start_date,
            SocialMedia.post_date <= end_date
        )
        
        prev_query = db.query(
            func.unnest(SocialMedia.hashtags).label('hashtag'),
            func.count('*').label('count')
        ).filter(
            SocialMedia.post_date > prev_start,
            SocialMedia.post_date <= start_date
        )
        
        filters = []
        if brand:
            filters.append(SocialMedia.brand == brand)
        if startDate and endDate:
            filters.append(SocialMedia.post_date.between(startDate, endDate))

        # Apply filters
        current_query = current_query.filter(*filters)
        prev_query = prev_query.filter(*filters)
        
        current_hashtags = current_query.group_by('hashtag').subquery()
        prev_hashtags = prev_query.group_by('hashtag').subquery()
        
        trending = db.query(
            current_hashtags.c.hashtag,
            current_hashtags.c.count,
            func.coalesce(prev_hashtags.c.count, 0).label('prev_count')
        ).outerjoin(
            prev_hashtags,
            current_hashtags.c.hashtag == prev_hashtags.c.hashtag
        ).order_by(
            current_hashtags.c.count.desc()
        ).limit(5).all()

        return [
            {
                "tag": hashtag,
                "count": count,
                "growth": f"+{round(((count - prev_count) / (prev_count if prev_count > 0 else 1)) * 100)}%"
            }
            for hashtag, count, prev_count in trending
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-comments")
def get_top_comments(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get top comments filtered by brand and date range"""
    try:
        # Base query
        query = db.query(
            SentimentSocialMedia
        ).join(
            SocialMedia,
            SocialMedia.social_media_post_id == SentimentSocialMedia.id_post
        )
        
        filters = []
        if brand:
            filters.append(SocialMedia.brand == brand)
        if startDate and endDate:
            filters.append(SocialMedia.post_date.between(startDate, endDate))

        # Apply filters
        query = query.filter(*filters)
        
        comments = query.order_by(
            SentimentSocialMedia.sentiment_score.desc()
        ).limit(5).all()
        
        return [
            {
                "comment": comment.comment,
                "sentiment_score": comment.sentiment_score,
                "total_likes": comment.total_likes,
                "total_replies": comment.total_replies
            }
            for comment in comments
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/content-sentiment")
def get_content_sentiment(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get content sentiment analysis filtered by brand and date range"""
    try:
        # Base query
        query = db.query(
            SocialMedia.jenis_konten,
            func.count(SentimentSocialMedia.id_post).label('total'),
            func.count(SentimentSocialMedia.id_post).filter(
                SentimentSocialMedia.sentiment_score > 0.5
            ).label('positive')
        ).join(
            SentimentSocialMedia,
            SocialMedia.social_media_post_id == SentimentSocialMedia.id_post
        )
        
        filters = []
        if brand:
            filters.append(SocialMedia.brand == brand)
        if startDate and endDate:
            filters.append(SocialMedia.post_date.between(startDate, endDate))

        # Apply filters
        query = query.filter(*filters)
        
        content_sentiment = query.group_by(
            SocialMedia.jenis_konten
        ).all()
        
        result = {}
        for content_type, total, positive in content_sentiment:
            negative = total - positive
            result[content_type] = {
                "positive": round((positive / total) * 100 if total > 0 else 0),
                "negative": round((negative / total) * 100 if total > 0 else 0)
            }
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
