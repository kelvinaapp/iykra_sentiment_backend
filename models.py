from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, ARRAY, JSON
from sqlalchemy.orm import relationship
from database import Base

class ProductCatalog(Base):
    __tablename__ = "product_catalog"
    
    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    brand = Column(String)
    subcategory = Column(String)
    color = Column(String)
    gender_orientation = Column(String)
    price = Column(Float)
    discount = Column(Float)
    rating = Column(Float)
    number_of_reviews = Column(Integer)
    product_lifecycle_status = Column(String)
    launch_date = Column(Date)
    trending_score = Column(Float)
    sustainability_rating = Column(Float)
    size_availability = Column(Boolean)
    terjual = Column(Integer)
    care_instructions = Column(String)
    origin = Column(String)
    sole_material = Column(String)
    upper_material = Column(String)
    
    reviews = relationship("Review", back_populates="product")

class Review(Base):
    __tablename__ = "reviewed_product"
    
    customer_review_id = Column(Integer, primary_key=True, index=True)
    review_date = Column(Date)
    review_text = Column(String)
    sentiment_score = Column(Float)
    keyword_tags = Column(ARRAY(String))
    emotion_score = Column(Float)
    rating = Column(Integer)
    helpful_votes = Column(Integer)
    customer_id = Column(Integer, ForeignKey("customer_demographics.customer_id"))
    product_id = Column(Integer, ForeignKey("product_catalog.product_id"))
    username = Column(String)
    nama_produk = Column(String)
    brand = Column(String)
    aspect_sentiments = Column(JSON)
    
    product = relationship("ProductCatalog", back_populates="reviews")
    customer = relationship("Customer")

class Customer(Base):
    __tablename__ = "customer_demographics"
    
    customer_id = Column(Integer, primary_key=True, index=True)
    age_group = Column(String)
    gender = Column(String)
    location = Column(String)

class Campaign(Base):
    __tablename__ = "campaign"
    
    campaign_id = Column(Integer, primary_key=True, index=True)
    name_campaign = Column(String, nullable=False)
    budget = Column(Float)
    reach = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    category = Column(String)
    format_type = Column(String)
    platform = Column(String)
    product_id = Column(Integer)
    target_engagement = Column(Integer)
    
    sentiment = relationship("CampaignSentiment", back_populates="campaign", uselist=False)

class CampaignSentiment(Base):
    __tablename__ = "sentiment_campaign"
    
    id_campaign = Column(Integer, ForeignKey("campaign.campaign_id"), primary_key=True)
    review_campaign = Column(String)
    sentiment_score = Column(Float)
    
    campaign = relationship("Campaign", back_populates="sentiment")

class SocialMediaExternalTrends(Base):
    __tablename__ = "social_media_external_trends"
    
    social_media_post_id = Column(Integer, primary_key=True, index=True)
    platform = Column(String)
    post_date = Column(Date)
    post_text = Column(String)
    engagement_count = Column(Integer)
    reach_count = Column(Integer)
    hashtags = Column(ARRAY(String))
    trend_score = Column(Float)
    brand = Column(String)
    collabs = Column(String)
    collabs_status = Column(String)
    jenis_konten = Column(String)
    
    sentiment = relationship("SentimentSocialMedia", back_populates="post", uselist=False)

class SentimentSocialMedia(Base):
    __tablename__ = "sentiment_social_media"
    
    id_post = Column(Integer, ForeignKey("social_media_external_trends.social_media_post_id"), primary_key=True)
    comment = Column(String)
    sentiment_score = Column(Float)
    total_likes = Column(Integer)
    total_replies = Column(Integer)
    
    post = relationship("SocialMediaExternalTrends", back_populates="sentiment")

class Sale(Base):
    __tablename__ = "sales"
    
    transaction_id = Column(Integer, primary_key=True, index=True)
    purchase_date = Column(Date)
    purchased_product_ids = Column(ARRAY(Integer))
    payment_method = Column(String)
    order_value = Column(Float)
    order_location = Column(String)
    repeat_purchase_score = Column(Float)
    return_rate = Column(Float)
    customer_id = Column(Integer, ForeignKey("customer_demographics.customer_id"))
    
    customer = relationship("Customer")
