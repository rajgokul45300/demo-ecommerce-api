# Demo E-Commerce API

A sample FastAPI application for demonstrating Azure SRE Agent capabilities.

## Features

- **E-Commerce Endpoints**: Products, Orders, Inventory
- **Health Check**: `/health` endpoint for monitoring
- **Bug Simulation**: Toggle 500 errors for demo purposes

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API status |
| `/health` | GET | Health check |
| `/api/products` | GET | List all products |
| `/api/products/{id}` | GET | Get product by ID |
| `/api/orders` | POST | Create order |
| `/api/inventory` | GET | Check inventory |
| `/demo/enable-bug` | POST | Enable 500 errors |
| `/demo/disable-bug` | POST | Disable 500 errors |
| `/demo/status` | GET | Check bug status |

## Demo Flow

1. Deploy app (healthy state)
2. Call `/demo/enable-bug` to simulate production issue
3. Azure Monitor detects 500 errors
4. SRE Agent investigates and proposes fix
5. Call `/demo/disable-bug` or rollback to fix

## Local Development

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Docker

```bash
docker build -t demo-ecommerce-api .
docker run -p 8000:8000 demo-ecommerce-api
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_BUG` | Enable 500 error mode | `false` |

