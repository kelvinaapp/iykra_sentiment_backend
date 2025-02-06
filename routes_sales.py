from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case, distinct
from datetime import datetime, timedelta
from typing import List, Dict, Any
from db.database import get_db
from db.models import Sales, SalesProducts, ProductCatalog, CustomerDemographics
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/sales",
    tags=["sales"]
)

@router.get("/")
def test_endpoint():
    return {"message": "Sales routes are working!"}

@router.get("/daily-sales")
async def get_daily_sales(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get daily sales data filtered by brand and date range"""
    try:
        if startDate and endDate:
            query_startDate = datetime.strptime(startDate, "%Y-%m-%d")
            query_endDate = datetime.strptime(endDate, "%Y-%m-%d")
        else:
            query_endDate = datetime.now()
            query_startDate = query_endDate - timedelta(days=7)

        query = db.query(
            func.date(Sales.purchase_date).label('day'),
            func.sum(Sales.order_value).label('orderValue')
        ).join(
            SalesProducts, Sales.transaction_id == SalesProducts.transaction_id
        ).join(
            ProductCatalog, SalesProducts.product_id == ProductCatalog.product_id
        ).filter(
            Sales.purchase_date.between(query_startDate, query_endDate)
        )

        if brand:
            query = query.filter(ProductCatalog.brand == brand)

        query = query.group_by(func.date(Sales.purchase_date))
        
        results = query.all()
        return [{"day": day.strftime("%a"), "orderValue": float(value)} for day, value in results]
    except Exception as e:
        logger.error(f"Error in /daily-sales endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/product-categories")
async def get_product_categories(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get sales volume by product category"""
    try:
        query = db.query(
            ProductCatalog.subcategory.label('category'),
            func.count(distinct(Sales.transaction_id)).label('volume')
        ).join(
            SalesProducts, ProductCatalog.product_id == SalesProducts.product_id
        ).join(
            Sales, SalesProducts.transaction_id == Sales.transaction_id
        )

        if brand:
            query = query.filter(ProductCatalog.brand == brand)
        if startDate and endDate:
            query = query.filter(Sales.purchase_date.between(startDate, endDate))

        query = query.group_by(ProductCatalog.subcategory).order_by(desc('volume'))
        
        results = query.all()
        return [{"category": category, "volume": volume} for category, volume in results]
    except Exception as e:
        logger.error(f"Error in /product-categories endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/return-rates")
async def get_return_rates(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get return rates by product category"""
    try:
        query = db.query(
            ProductCatalog.subcategory.label('category'),
            (func.avg(Sales.return_rate) * 100.0).label('value')
        ).join(
            SalesProducts, ProductCatalog.product_id == SalesProducts.product_id
        ).join(
            Sales, SalesProducts.transaction_id == Sales.transaction_id
        )

        if brand:
            query = query.filter(ProductCatalog.brand == brand)
        if startDate and endDate:
            query = query.filter(Sales.purchase_date.between(startDate, endDate))

        query = query.group_by(ProductCatalog.subcategory)
        
        results = query.all()
        return [{"category": category, "value": float(value)} for category, value in results]
    except Exception as e:
        logger.error(f"Error in /return-rates endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer-locations")
async def get_customer_locations(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get customer count by city"""
    try:
        query = db.query(
            CustomerDemographics.location.label('city'),
            func.count(distinct(CustomerDemographics.customer_id)).label('customers')
        ).join(
            Sales, CustomerDemographics.customer_id == Sales.customer_id
        ).join(
            SalesProducts, Sales.transaction_id == SalesProducts.transaction_id
        ).join(
            ProductCatalog, SalesProducts.product_id == ProductCatalog.product_id
        )

        if brand:
            query = query.filter(ProductCatalog.brand == brand)
        if startDate and endDate:
            query = query.filter(Sales.purchase_date.between(startDate, endDate))

        query = query.group_by(CustomerDemographics.location).order_by(desc('customers')).limit(10)
        
        results = query.all()
        return [{"city": city, "customers": customers} for city, customers in results]
    except Exception as e:
        logger.error(f"Error in /customer-locations endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/demographics")
async def get_demographics(
    brand: str = Query(None, description="Brand name to filter data"),
    startDate: str = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    endDate: str = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get customer demographics (gender and age distribution)"""
    try:
        # Base subquery to get distinct customers
        base_query = db.query(
            CustomerDemographics.customer_id,
            CustomerDemographics.gender,
            CustomerDemographics.age_group
        ).join(
            Sales, CustomerDemographics.customer_id == Sales.customer_id
        ).join(
            SalesProducts, Sales.transaction_id == SalesProducts.transaction_id
        ).join(
            ProductCatalog, SalesProducts.product_id == ProductCatalog.product_id
        )

        if brand:
            base_query = base_query.filter(ProductCatalog.brand == brand)
        if startDate and endDate:
            base_query = base_query.filter(Sales.purchase_date.between(startDate, endDate))

        # Get distinct customers subquery
        distinct_customers = base_query.distinct().subquery()

        # Gender distribution
        total_customers = db.query(func.count(distinct(distinct_customers.c.customer_id))).scalar()
        
        gender_query = db.query(
            distinct_customers.c.gender.label('name'),
            (func.count(distinct_customers.c.customer_id) * 100.0 / total_customers).label('value')
        ).group_by(distinct_customers.c.gender)
        
        gender_results = gender_query.all()
        gender_data = [{"name": name, "value": float(value)} for name, value in gender_results]

        # Age distribution
        age_query = db.query(
            distinct_customers.c.age_group.label('group'),
            (func.count(distinct_customers.c.customer_id) * 100.0 / total_customers).label('value')
        ).group_by(distinct_customers.c.age_group)
        
        age_results = age_query.all()
        age_data = [{"group": group, "value": float(value)} for group, value in age_results]

        return {
            "gender": gender_data,
            "age": age_data
        }
    except Exception as e:
        logger.error(f"Error in /demographics endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))