"""
Demo E-Commerce API for Azure SRE Agent
This API simulates an e-commerce service with endpoints that can be "broken"
to demonstrate SRE Agent's incident detection and remediation capabilities.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime
import random

# Configure logging for Application Insights
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Demo E-Commerce API",
    description="Sample API for Azure SRE Agent Demo",
    version="1.0.0"
)

# Simulated product database
PRODUCTS = [
    {"id": 1, "name": "Laptop", "price": 999.99, "stock": 50},
    {"id": 2, "name": "Smartphone", "price": 699.99, "stock": 100},
    {"id": 3, "name": "Headphones", "price": 199.99, "stock": 200},
    {"id": 4, "name": "Tablet", "price": 449.99, "stock": 75},
    {"id": 5, "name": "Smartwatch", "price": 299.99, "stock": 150},
]

# Feature flag to simulate bugs (controlled by environment variable)
BUG_ENABLED = os.getenv("ENABLE_BUG", "false").lower() == "true"


@app.get("/")
async def root():
    """Home endpoint - shows API status"""
    return {
        "service": "Demo E-Commerce API",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "bug_mode": BUG_ENABLED
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/products")
async def get_products():
    """Get all products - main e-commerce endpoint"""
    logger.info("Fetching all products")
    
    # Simulate bug: 500 error when BUG_ENABLED is true
    if BUG_ENABLED:
        logger.error("BUG: Database connection failed!")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error: Database connection failed"
        )
    
    return {
        "success": True,
        "count": len(PRODUCTS),
        "products": PRODUCTS
    }


@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    """Get a specific product by ID"""
    logger.info(f"Fetching product {product_id}")
    
    # Simulate bug: 500 error when BUG_ENABLED is true
    if BUG_ENABLED:
        logger.error(f"BUG: Failed to fetch product {product_id}!")
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: Failed to fetch product {product_id}"
        )
    
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"success": True, "product": product}


@app.post("/api/orders")
async def create_order(request: Request):
    """Create a new order - simulates order processing"""
    logger.info("Creating new order")
    
    # Simulate bug: 500 error when BUG_ENABLED is true
    if BUG_ENABLED:
        logger.error("BUG: Order processing failed!")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error: Order processing failed"
        )
    
    return {
        "success": True,
        "order_id": f"ORD-{random.randint(10000, 99999)}",
        "status": "created",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/inventory")
async def get_inventory():
    """Get inventory status - for dependency mapping demo"""
    logger.info("Checking inventory")
    
    if BUG_ENABLED:
        logger.error("BUG: Inventory service unavailable!")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error: Inventory service unavailable"
        )
    
    return {
        "success": True,
        "total_items": sum(p["stock"] for p in PRODUCTS),
        "low_stock_items": [p for p in PRODUCTS if p["stock"] < 100]
    }


# Manual trigger endpoints for demo purposes
@app.post("/demo/enable-bug")
async def enable_bug():
    """Enable bug mode (for demo - triggers 500 errors)"""
    global BUG_ENABLED
    BUG_ENABLED = True
    logger.warning("BUG MODE ENABLED - API will return 500 errors!")
    return {"message": "Bug mode enabled", "bug_enabled": True}


@app.post("/demo/disable-bug")
async def disable_bug():
    """Disable bug mode (for demo - restores normal operation)"""
    global BUG_ENABLED
    BUG_ENABLED = False
    logger.info("Bug mode disabled - API restored to normal")
    return {"message": "Bug mode disabled", "bug_enabled": False}


@app.get("/demo/status")
async def demo_status():
    """Check current demo status"""
    return {
        "bug_enabled": BUG_ENABLED,
        "message": "API will return 500 errors" if BUG_ENABLED else "API is operating normally"
    }


# Exception handler for logging
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

