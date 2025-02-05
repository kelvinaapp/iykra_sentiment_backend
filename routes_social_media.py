from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List, Dict, Any
from db.database import get_db
from db.models import SocialMediaExternalTrends, SentimentSocialMedia, Campaign
import schemas
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/social-media",
    tags=["social-media"]
)

@router.get("/")
def test_endpoint():
    return {"message": "Social media routes are working!"}

@router.get("/metrics")
def get_engagement_metrics(
    brand: str = Query(None, description="Brand name to filter data"),
    start_date: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get overall social media engagement metrics filtered by brand and date range"""
    logger.info(f"Processing /metrics endpoint request for brand: {brand}, date range: {start_date} to {end_date}")
    try:
        # Base queries
        engagement_query = db.query(
            func.sum(SentimentSocialMedia.total_likes + SentimentSocialMedia.total_replies)
        )
        reach_query = db.query(
            func.sum(SocialMediaExternalTrends.reach_count)
        )
        posts_query = db.query(SocialMediaExternalTrends)
        
        # Apply brand filter if provided
        if brand:
            engagement_query = engagement_query.join(
                SocialMediaExternalTrends,
                SocialMediaExternalTrends.social_media_post_id == SentimentSocialMedia.id_post
            ).filter(SocialMediaExternalTrends.brand == brand)
            
            reach_query = reach_query.filter(SocialMediaExternalTrends.brand == brand)
            posts_query = posts_query.filter(SocialMediaExternalTrends.brand == brand)
        
        # Apply date filters if provided
        if start_date and end_date:
            engagement_query = engagement_query.join(
                SocialMediaExternalTrends,
                SocialMediaExternalTrends.social_media_post_id == SentimentSocialMedia.id_post
            ).filter(SocialMediaExternalTrends.post_date.between(start_date, end_date))
            
            reach_query = reach_query.filter(SocialMediaExternalTrends.post_date.between(start_date, end_date))
            posts_query = posts_query.filter(SocialMediaExternalTrends.post_date.between(start_date, end_date))
        
        total_engagement = engagement_query.scalar() or 0
        total_reach = reach_query.scalar() or 0
        total_posts = posts_query.count()
        
        total_impressions = total_reach * 1.5  # Estimated impression rate
        
        response = {
            "totalEngagement": f"{total_engagement/1000:.1f}K",
            "reach": f"{total_reach/1000:.1f}K",
            "impressions": f"{total_impressions/1000:.1f}K",
            "totalPosts": str(total_posts)
        }
        logger.info(f"Returning metrics response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in /metrics endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeseries")
async def get_timeseries_data(
    brand: str = Query(None, description="Brand name to filter data"),
    start_date: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get daily engagement and reach data filtered by brand and date range"""
    logger.info(f"Processing /timeseries endpoint request for brand: {brand}, date range: {start_date} to {end_date}")
    try:
        # Use provided date range or default to last 7 days
        if start_date and end_date:
            query_start_date = datetime.strptime(start_date, "%Y-%m-%d")
            query_end_date = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            query_end_date = datetime.now() - timedelta(days=1)
            query_start_date = query_end_date - timedelta(days=7)
        
        # Base query
        query = db.query(
            func.date(SocialMediaExternalTrends.post_date).label('date'),
            func.sum(SentimentSocialMedia.total_likes + SentimentSocialMedia.total_replies).label('engagement'),
            func.sum(SocialMediaExternalTrends.reach_count).label('reach')
        ).join(
            SentimentSocialMedia,
            SocialMediaExternalTrends.social_media_post_id == SentimentSocialMedia.id_post
        ).filter(
            SocialMediaExternalTrends.post_date.between(query_start_date, query_end_date)
        )
        
        # Apply brand filter if provided
        if brand:
            query = query.filter(SocialMediaExternalTrends.brand == brand)
        
        daily_stats = query.group_by(
            func.date(SocialMediaExternalTrends.post_date)
        ).all()
        
        days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        engagement_data = [0] * 7
        reach_data = [0] * 7
        
        for stat in daily_stats:
            day_idx = stat.date.weekday()
            engagement_data[day_idx] = float(stat.engagement)
            reach_data[day_idx] = float(stat.reach * 100)
        
        response = {
            "labels": days,
            "datasets": [
                {
                    "label": "Engagement",
                    "data": engagement_data,
                    "borderColor": "#4caf50",
                    "tension": 0.4
                },
                {
                    "label": "Reach",
                    "data": reach_data,
                    "borderColor": "#2196f3",
                    "tension": 0.4
                }
            ]
        }
        return response
    except Exception as e:
        logger.error(f"Error in /timeseries endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/content-performance")
async def get_content_performance(
    brand: str = Query(None, description="Brand name to filter data"),
    start_date: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get engagement and reach rates by content type filtered by brand and date range"""
    logger.info(f"Processing /content-performance endpoint request for brand: {brand}, date range: {start_date} to {end_date}")
    try:
        query = db.query(
            SocialMediaExternalTrends.jenis_konten,
            (func.sum(SentimentSocialMedia.total_likes + SentimentSocialMedia.total_replies) * 100.0 / 
             func.count(SocialMediaExternalTrends.social_media_post_id)).label('engagement_rate'),
            (func.sum(SocialMediaExternalTrends.reach_count) * 100.0 / 
             func.count(SocialMediaExternalTrends.social_media_post_id)).label('reach_rate')
        ).join(
            SentimentSocialMedia,
            SocialMediaExternalTrends.social_media_post_id == SentimentSocialMedia.id_post
        )

        if brand:
            query = query.filter(SocialMediaExternalTrends.brand == brand)
            
        if start_date and end_date:
            query = query.filter(SocialMediaExternalTrends.post_date.between(start_date, end_date))
        
        performance = query.group_by(
            SocialMediaExternalTrends.jenis_konten
        ).all()
        
        response = {
            "labels": [p.jenis_konten for p in performance],
            "datasets": [
                {
                    "label": "Engagement Rate",
                    "data": [float(p.engagement_rate) for p in performance],
                    "backgroundColor": "#00695c"
                },
                {
                    "label": "Reach Rate",
                    "data": [float(p.reach_rate) for p in performance],
                    "backgroundColor": "#2196f3"
                }
            ]
        }
        return response
    except Exception as e:
        logger.error(f"Error in /content-performance endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platform-performance")
async def get_platform_performance(
    brand: str = Query(None, description="Brand name to filter data"),
    start_date: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get reach and engagement metrics by platform filtered by brand and date range"""
    logger.info(f"Processing /platform-performance endpoint request for brand: {brand}, date range: {start_date} to {end_date}")
    try:
        query = db.query(
            SocialMediaExternalTrends.platform,
            func.sum(SentimentSocialMedia.total_likes + SentimentSocialMedia.total_replies).label('engagement'),
            func.sum(SocialMediaExternalTrends.reach_count).label('reach')
        ).join(
            SentimentSocialMedia,
            SocialMediaExternalTrends.social_media_post_id == SentimentSocialMedia.id_post
        )

        if brand:
            query = query.filter(SocialMediaExternalTrends.brand == brand)
            
        if start_date and end_date:
            query = query.filter(SocialMediaExternalTrends.post_date.between(start_date, end_date))
        
        platform_stats = query.group_by(
            SocialMediaExternalTrends.platform
        ).all()
        
        platform_data = []
        total_platform_reach = sum(float(platform.reach or 0) for platform in platform_stats)
        total_platform_engagement = sum(float(platform.engagement or 0) for platform in platform_stats)
        
        for platform in platform_stats:
            platform_reach = float(platform.reach or 0)
            platform_engagement = float(platform.engagement or 0)
            
            reach_percentage = (platform_reach / total_platform_reach * 100) if total_platform_reach > 0 else 0
            engagement_percentage = (platform_engagement / total_platform_engagement * 100) if total_platform_engagement > 0 else 0
            
            platform_data.append({
                'platform': platform.platform,
                'reach_percentage': round(reach_percentage, 1),
                'engagement_percentage': round(engagement_percentage, 1)
            })
        
        response = {
            'labels': ['Reach', 'Engagement'],
            'datasets': [
                {
                    'label': p['platform'],
                    'data': [p['reach_percentage'], p['engagement_percentage']],
                    'backgroundColor': '#4caf50' if p['platform'] == 'Instagram' else '#2196f3'
                } for p in platform_data
            ]
        }
        return response
    except Exception as e:
        logger.error(f"Error in /platform-performance endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-posts/reach")
async def get_top_posts_by_reach(
    brand: str = Query(None, description="Brand name to filter data"),
    start_date: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get top 5 posts by reach filtered by brand and date range"""
    logger.info(f"Processing /top-posts/reach endpoint request for brand: {brand}, date range: {start_date} to {end_date}")
    try:
        # Base query
        query = db.query(
            SocialMediaExternalTrends,
            (SentimentSocialMedia.total_likes + SentimentSocialMedia.total_replies).label('total_engagement')
        ).join(
            SentimentSocialMedia,
            SocialMediaExternalTrends.social_media_post_id == SentimentSocialMedia.id_post
        )
        
        # Apply brand filter if provided
        if brand:
            query = query.filter(SocialMediaExternalTrends.brand == brand)
        
        # Apply date filters if provided
        if start_date and end_date:
            query = query.filter(SocialMediaExternalTrends.post_date.between(start_date, end_date))
        
        posts = query.order_by(
            desc(SocialMediaExternalTrends.reach_count)
        ).limit(5).all()
        
        result = []
        for post, engagement in posts:
            result.append({
                "caption": post.post_text,
                "type": post.jenis_konten,
                "timestamp": post.post_date.strftime("%Y-%m-%d %H:%M"),
                "engagement": engagement,
                "reach": post.reach_count,
                "platform": post.platform,
                "collabs": post.collabs,
                "hashtags": post.hashtags
            })
        logger.info(f"Returning top-posts/reach response: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in /top-posts/reach endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-posts/engagement")
async def get_top_posts_by_engagement(
    brand: str = Query(None, description="Brand name to filter data"),
    start_date: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get top 5 posts by engagement filtered by brand and date range"""
    logger.info(f"Processing /top-posts/engagement endpoint request for brand: {brand}, date range: {start_date} to {end_date}")
    try:
        # Base query
        query = db.query(
            SocialMediaExternalTrends,
            (SentimentSocialMedia.total_likes + SentimentSocialMedia.total_replies).label('total_engagement')
        ).join(
            SentimentSocialMedia,
            SocialMediaExternalTrends.social_media_post_id == SentimentSocialMedia.id_post
        )
        
        # Apply brand filter if provided
        if brand:
            query = query.filter(SocialMediaExternalTrends.brand == brand)
        
        # Apply date filters if provided
        if start_date and end_date:
            query = query.filter(SocialMediaExternalTrends.post_date.between(start_date, end_date))
        
        top_posts = query.order_by(
            desc('total_engagement')
        ).limit(5).all()
        
        result = []
        for post, engagement in top_posts:
            result.append({
                "caption": post.post_text,
                "type": post.jenis_konten,
                "timestamp": post.post_date.strftime("%Y-%m-%d %H:%M"),
                "engagement": engagement,
                "platform": post.platform,
                "collabs": post.collabs,
                "hashtags": post.hashtags
            })
        logger.info(f"Returning top-posts/engagement response: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in /top-posts/engagement endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-hashtags")
async def get_top_hashtags(
    brand: str = Query(None, description="Brand name to filter data"),
    start_date: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get top hashtags by reach and engagement filtered by brand and date range"""
    logger.info(f"Processing /top-hashtags endpoint request for brand: {brand}, date range: {start_date} to {end_date}")
    try:
        # Using array_elements to unnest hashtags array
        reach_hashtags = db.query(
            func.unnest(SocialMediaExternalTrends.hashtags).label('hashtag'),
            func.sum(SocialMediaExternalTrends.reach_count).label('reach'),
            func.count(SocialMediaExternalTrends.social_media_post_id).label('count')
        ).filter(
            SocialMediaExternalTrends.brand == brand
        ).filter(
            SocialMediaExternalTrends.post_date.between(start_date, end_date)
        ).group_by(
            'hashtag'
        ).order_by(
            desc('reach')
        ).limit(5).all()

        engagement_hashtags = db.query(
            func.unnest(SocialMediaExternalTrends.hashtags).label('hashtag'),
            func.sum(SentimentSocialMedia.total_likes + SentimentSocialMedia.total_replies).label('engagement'),
            func.count(SocialMediaExternalTrends.social_media_post_id).label('count')
        ).join(
            SentimentSocialMedia,
            SocialMediaExternalTrends.social_media_post_id == SentimentSocialMedia.id_post
        ).filter(
            SocialMediaExternalTrends.brand == brand
        ).filter(
            SocialMediaExternalTrends.post_date.between(start_date, end_date)
        ).group_by(
            'hashtag'
        ).order_by(
            desc('engagement')
        ).limit(5).all()

        reach_result = [
            {
                "tag": tag,
                "reach": reach,
                "count": count
            }
            for tag, reach, count in reach_hashtags
        ]

        engagement_result = [
            {
                "tag": tag,
                "engagement": engagement,
                "count": count
            }
            for tag, engagement, count in engagement_hashtags
        ]

        return {
            "byReach": reach_result,
            "byEngagement": engagement_result
        }
    except Exception as e:
        logger.error(f"Error in /top-hashtags endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-collaborators")
async def get_top_collaborators(
    brand: str = Query(None, description="Brand name to filter data"),
    start_date: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get top collaborators by reach and engagement filtered by brand and date range"""
    logger.info(f"Processing /top-collaborators endpoint request for brand: {brand}, date range: {start_date} to {end_date}")
    try:
        # Get top collaborators by reach
        reach_collabs = db.query(
            SocialMediaExternalTrends.collabs,
            func.sum(SocialMediaExternalTrends.reach_count).label('reach'),
            func.count(SocialMediaExternalTrends.social_media_post_id).label('posts')
        ).filter(
            SocialMediaExternalTrends.brand == brand
        ).filter(
            SocialMediaExternalTrends.post_date.between(start_date, end_date)
        ).filter(
            SocialMediaExternalTrends.collabs.isnot(None)
        ).group_by(
            SocialMediaExternalTrends.collabs
        ).order_by(
            desc('reach')
        ).limit(5).all()

        # Get top collaborators by engagement
        engagement_collabs = db.query(
            SocialMediaExternalTrends.collabs,
            func.sum(SentimentSocialMedia.total_likes + SentimentSocialMedia.total_replies).label('engagement'),
            func.count(SocialMediaExternalTrends.social_media_post_id).label('posts')
        ).join(
            SentimentSocialMedia,
            SocialMediaExternalTrends.social_media_post_id == SentimentSocialMedia.id_post
        ).filter(
            SocialMediaExternalTrends.brand == brand
        ).filter(
            SocialMediaExternalTrends.post_date.between(start_date, end_date)
        ).filter(
            SocialMediaExternalTrends.collabs.isnot(None)
        ).group_by(
            SocialMediaExternalTrends.collabs
        ).order_by(
            desc('engagement')
        ).limit(5).all()

        reach_result = [
            {
                "tag": collab,
                "reach": reach,
                "posts": posts
            }
            for collab, reach, posts in reach_collabs
        ]

        engagement_result = [
            {
                "tag": collab,
                "engagement": engagement,
                "posts": posts
            }
            for collab, engagement, posts in engagement_collabs
        ]

        return {
            "byReach": reach_result,
            "byEngagement": engagement_result
        }
    except Exception as e:
        logger.error(f"Error in /top-collaborators endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
