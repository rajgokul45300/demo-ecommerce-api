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
import time

# ============================================
# Application Insights Configuration
# ============================================
APPINSIGHTS_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")

# Setup Azure Monitor/Application Insights tracing
if APPINSIGHTS_CONNECTION_STRING:
    try:
        from opencensus.ext.azure.trace_exporter import AzureExporter
        from opencensus.ext.azure.log_exporter import AzureLogHandler
        from opencensus.trace.samplers import AlwaysOnSampler
        from opencensus.trace.tracer import Tracer
        from opencensus.trace import config_integration
        
        # Enable logging integration
        config_integration.trace_integrations(['logging'])
        
        # Create tracer with Azure exporter
        tracer = Tracer(
            exporter=AzureExporter(connection_string=APPINSIGHTS_CONNECTION_STRING),
            sampler=AlwaysOnSampler()
        )
        
        # Configure logging to send to Application Insights
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Add Azure handler for logs
        azure_handler = AzureLogHandler(connection_string=APPINSIGHTS_CONNECTION_STRING)
        azure_handler.setLevel(logging.INFO)
        logger.addHandler(azure_handler)
        
        # Also add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        
        APPINSIGHTS_ENABLED = True
        logger.info("Application Insights integration enabled successfully!")
        
    except Exception as e:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to initialize Application Insights: {e}")
        APPINSIGHTS_ENABLED = False
        tracer = None
else:
    # Fallback logging when no connection string
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Application Insights not configured - using console logging only")
    APPINSIGHTS_ENABLED = False
    tracer = None

# ============================================
# FastAPI App Setup
# ============================================
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

# Feature flag to simulate bugs (controlled by environment variable or toggle)
BUG_ENABLED = os.getenv("ENABLE_BUG", "false").lower() == "true"


# ============================================
# Middleware for Request Tracking
# ============================================
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Middleware to track all requests for Application Insights"""
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"Request started: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log request completion with status
        if response.status_code >= 500:
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Duration: {duration:.3f}s"
            )
        elif response.status_code >= 400:
            logger.warning(
                f"Request client error: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Duration: {duration:.3f}s"
            )
        else:
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Duration: {duration:.3f}s"
            )
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.exception(
            f"Request exception: {request.method} {request.url.path} "
            f"- Error: {str(e)} - Duration: {duration:.3f}s"
        )
        raise


# ============================================
# API Endpoints
# ============================================
@app.get("/")
async def root():
    """Home endpoint - shows API status"""
    return {
        "service": "Demo E-Commerce API",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "bug_mode": BUG_ENABLED,
        "appinsights_enabled": APPINSIGHTS_ENABLED
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "appinsights": "connected" if APPINSIGHTS_ENABLED else "not configured"
    }


@app.get("/api/products")
async def get_products():
    """Get all products - main e-commerce endpoint"""
    logger.info("Fetching all products")
    
    # BUG INTRODUCED IN THIS COMMIT - Issue #42
    # Developer accidentally added database validation that always fails
    # This simulates a real production bug from a code change
    db_connection_status = None  # Bug: This should be initialized to True
    
    if not db_connection_status:
        logger.error("CRITICAL: Database connection validation failed! db_connection_status is None")
        logger.error("This bug was introduced in commit - check git history for recent changes")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error: Database connection validation failed"
        )
    
    # Simulate bug: 500 error when BUG_ENABLED is true
    if BUG_ENABLED:
        logger.error("CRITICAL: Database connection failed! BUG_ENABLED=true causing 500 error")
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
        logger.error(f"CRITICAL: Failed to fetch product {product_id}! BUG_ENABLED=true")
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
        logger.error("CRITICAL: Order processing failed! BUG_ENABLED=true")
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
        logger.error("CRITICAL: Inventory service unavailable! BUG_ENABLED=true")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error: Inventory service unavailable"
        )
    
    return {
        "success": True,
        "total_items": sum(p["stock"] for p in PRODUCTS),
        "low_stock_items": [p for p in PRODUCTS if p["stock"] < 100]
    }


# ============================================
# Demo Control Endpoints
# ============================================
@app.post("/demo/enable-bug")
async def enable_bug():
    """Enable bug mode (for demo - triggers 500 errors)"""
    global BUG_ENABLED
    BUG_ENABLED = True
    logger.warning("⚠️ BUG MODE ENABLED - API will return 500 errors!")
    logger.error("SIMULATED BUG ACTIVATED - This is a demo error for SRE Agent testing")
    return {"message": "Bug mode enabled", "bug_enabled": True}


@app.post("/demo/disable-bug")
async def disable_bug():
    """Disable bug mode (for demo - restores normal operation)"""
    global BUG_ENABLED
    BUG_ENABLED = False
    logger.info("✅ Bug mode disabled - API restored to normal operation")
    return {"message": "Bug mode disabled", "bug_enabled": False}


@app.get("/demo/status")
async def demo_status():
    """Check current demo status"""
    return {
        "bug_enabled": BUG_ENABLED,
        "appinsights_enabled": APPINSIGHTS_ENABLED,
        "message": "API will return 500 errors" if BUG_ENABLED else "API is operating normally"
    }


# ============================================
# Exception Handlers
# ============================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler that logs to Application Insights"""
    logger.error(
        f"HTTP Exception: Status={exc.status_code}, "
        f"Detail={exc.detail}, Path={request.url.path}, "
        f"Method={request.method}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler for unexpected errors"""
    logger.exception(
        f"Unhandled Exception: {type(exc).__name__}: {str(exc)}, "
        f"Path={request.url.path}, Method={request.method}"
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "status_code": 500,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
