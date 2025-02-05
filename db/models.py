from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, ARRAY, JSON, DECIMAL, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database import Base

class ProductCatalog(Base):
    __tablename__ = "product_catalog"
    
    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False)
    brand = Column(String(100))
    subcategory = Column(String(100))
    color = Column(String(50))
    gender_orientation = Column(String(50))
    price = Column(DECIMAL)
    discount = Column(DECIMAL)
    rating = Column(DECIMAL)
    number_of_reviews = Column(Integer)
    product_lifecycle_status = Column(String(50))
    launch_date = Column(Date)
    trending_score = Column(DECIMAL)
    sustainability_rating = Column(DECIMAL)
    size_availability = Column(Boolean)
    terjual = Column(Integer)
    care_instructions = Column(Text)
    origin = Column(String(100))
    sole_material = Column(String(100))
    upper_material = Column(String(100))
    
    reviews = relationship("ReviewedProduct", back_populates="product")
    sales = relationship("SaleProduct", back_populates="product")
    campaigns = relationship("Campaign", back_populates="product")

class ReviewedProduct(Base):
    __tablename__ = "reviewed_product"
    
    customer_review_id = Column(Integer, primary_key=True, index=True)
    review_date = Column(Date)
    review_text = Column(Text)
    sentiment_score = Column(DECIMAL)
    keyword_tags = Column(ARRAY(String))
    emotion_score = Column(DECIMAL)
    rating = Column(Integer)
    helpful_votes = Column(Integer)
    customer_id = Column(Integer, ForeignKey("customer_demographics.customer_id"))
    product_id = Column(Integer, ForeignKey("product_catalog.product_id"))
    username = Column(String(100))
    nama_produk = Column(String(255))
    brand = Column(String(100))
    aspect_sentiments = Column(JSONB)
    
    product = relationship("ProductCatalog", back_populates="reviews")
    customer = relationship("CustomerDemographics", back_populates="reviews")

class CustomerDemographics(Base):
    __tablename__ = "customer_demographics"
    
    customer_id = Column(Integer, primary_key=True, index=True)
    age_group = Column(String(50))
    gender = Column(String(50))
    location = Column(String(255))
    
    reviews = relationship("ReviewedProduct", back_populates="customer")
    sales = relationship("Sale", back_populates="customer")

class Campaign(Base):
    __tablename__ = "campaign"
    
    campaign_id = Column(Integer, primary_key=True, index=True)
    name_campaign = Column(String(255), nullable=False)
    budget = Column(DECIMAL)
    reach = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    category = Column(String(100))
    format_type = Column(String(100))
    platform = Column(String(100))
    product_id = Column(Integer, ForeignKey("product_catalog.product_id"))
    target_engagement = Column(Integer)
    
    product = relationship("ProductCatalog", back_populates="campaigns")
    sentiment = relationship("SentimentCampaign", back_populates="campaign", uselist=False)

class SentimentCampaign(Base):
    __tablename__ = "sentiment_campaign"
    
    id_campaign = Column(Integer, ForeignKey("campaign.campaign_id"), primary_key=True)
    review_campaign = Column(String)
    sentiment_score = Column(DECIMAL)
    
    campaign = relationship("Campaign", back_populates="sentiment")

class SocialMedia(Base):
    __tablename__ = "social_media"
    
    social_media_post_id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(100))
    post_date = Column(Date)
    post_text = Column(Text)
    engagement_count = Column(Integer)
    reach_count = Column(Integer)
    hashtags = Column(ARRAY(String))
    trend_score = Column(DECIMAL)
    brand = Column(String(100))
    sentiment = relationship("SentimentSocialMedia", back_populates="post", uselist=False)

class SentimentSocialMedia(Base):
    __tablename__ = "sentiment_social_media"
    
    id_post = Column(Integer, ForeignKey("social_media.social_media_post_id"), primary_key=True)
    comment = Column(Text)
    sentiment_score = Column(DECIMAL)
    total_likes = Column(Integer)
    total_replies = Column(Integer)
    
    post = relationship("SocialMedia", back_populates="sentiment")

class Sale(Base):
    __tablename__ = "sales"
    
    transaction_id = Column(Integer, primary_key=True, index=True)
    purchase_date = Column(Date)
    payment_method = Column(String)
    order_value = Column(Float)
    order_location = Column(String)
    repeat_purchase_score = Column(Float)
    return_rate = Column(Float)
    customer_id = Column(Integer, ForeignKey("customer_demographics.customer_id"))
    
    customer = relationship("CustomerDemographics", back_populates="sales")
    products = relationship("SaleProduct", back_populates="sale")

class SaleProduct(Base):
    __tablename__ = "sale_product"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("sales.transaction_id"))
    product_id = Column(Integer, ForeignKey("product_catalog.product_id"))
    
    sale = relationship("Sale", back_populates="products")
    product = relationship("ProductCatalog", back_populates="sales")

class SustainabilityIntegration(Base):
    __tablename__ = "sustainability_integration"
    
    column_name = Column(String(255), primary_key=True)
    eco_friendly_keyword_usage = Column(ARRAY(String))
    sustainability_sentiment_score = Column(DECIMAL)
