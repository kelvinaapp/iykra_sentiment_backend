from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date

class BaseModelConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

class ProductBase(BaseModelConfig):
    product_name: str
    brand: str
    subcategory: str
    price: float
    rating: float

class Product(ProductBase):
    product_id: int
    color: str
    gender_orientation: str
    discount: float
    number_of_reviews: int
    trending_score: float

class ProductDetail(BaseModelConfig):
    product_lifecycle_status: str
    launch_date: date
    sustainability_rating: float
    size_availability: bool

class ReviewBase(BaseModelConfig):
    review_text: str
    sentiment_score: float
    rating: int

class Review(ReviewBase):
    customer_review_id: int
    review_date: date
    keyword_tags: List[str]
    emotion_score: float
    helpful_votes: int

class BrandSentiment(BaseModelConfig):
    brand: str
    average_sentiment: float
    total_reviews: int

class ProductSentiment(BaseModelConfig):
    product_id: int
    average_sentiment: float
    total_reviews: int
    reviews: List[Review]

class CampaignBase(BaseModel):
    name_campaign: str
    budget: float
    platform: str

class Campaign(CampaignBase):
    campaign_id: int
    reach: int
    start_date: date
    end_date: date
    target_engagement: int

class CampaignDetail(BaseModelConfig):
    category: str
    format_type: str  
    product_id: int
    sentiment_score: Optional[float]

class BrandComparison(BaseModelConfig):
    brand: str
    average_sentiment: float
    total_reviews: int

class TrendingProduct(BaseModelConfig):
    product_id: int
    product_name: str
    brand: str
    trending_score: float
    number_of_reviews: int
    average_sentiment: Optional[float]

class SocialMediaExternalTrendsBase(BaseModel):
    platform: str
    post_date: date
    post_text: str
    engagement_count: int
    reach_count: int
    hashtags: List[str]
    trend_score: float
    brand: str
    collabs: str
    collabs_status: str
    jenis_konten: str

class SocialMediaExternalTrendsCreate(SocialMediaExternalTrendsBase):
    pass

class SocialMediaExternalTrends(SocialMediaExternalTrendsBase):
    social_media_post_id: int

    class Config:
        orm_mode = True

class SentimentSocialMediaBase(BaseModel):
    comment: str
    sentiment_score: float
    total_likes: int
    total_replies: int

class SentimentSocialMediaCreate(SentimentSocialMediaBase):
    id_post: int

class SentimentSocialMedia(SentimentSocialMediaBase):
    id_post: int

    class Config:
        orm_mode = True

class CampaignBase(BaseModel):
    name_campaign: str
    budget: Optional[float] = None
    reach: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    category: Optional[str] = None
    format_type: Optional[str] = None
    platform: Optional[str] = None
    product_id: Optional[int] = None
    target_engagement: Optional[int] = None

class CampaignCreate(CampaignBase):
    pass

class Campaign(CampaignBase):
    campaign_id: int

    class Config:
        orm_mode = True

class ProductCatalogBase(BaseModel):
    product_name: str
    brand: Optional[str] = None
    subcategory: Optional[str] = None
    color: Optional[str] = None
    gender_orientation: Optional[str] = None
    price: Optional[float] = None
    discount: Optional[float] = None
    rating: Optional[float] = None
    number_of_reviews: Optional[int] = None
    product_lifecycle_status: Optional[str] = None
    launch_date: Optional[date] = None
    trending_score: Optional[float] = None
    sustainability_rating: Optional[float] = None
    size_availability: Optional[bool] = None
    terjual: Optional[int] = None
    care_instructions: Optional[str] = None
    origin: Optional[str] = None
    sole_material: Optional[str] = None
    upper_material: Optional[str] = None

class ProductCatalogCreate(ProductCatalogBase):
    pass

class ProductCatalog(ProductCatalogBase):
    product_id: int

    class Config:
        orm_mode = True
