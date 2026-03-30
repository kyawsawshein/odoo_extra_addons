# Connection Guide for API Module

## Connection Error Solution

The error `Connection refused` means the odoo_api service is not running or not accessible from your Odoo instance.

## Step 1: Start the odoo_api Service

### Option A: Using Docker Compose
```bash
cd odoo_api
docker-compose up -d
```

### Option B: Using Python directly
```bash
cd odoo_api
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Step 2: Verify Service is Running

Check if the service is accessible:
```bash
curl http://localhost:8000/docs
```

You should see the FastAPI documentation page.

## Step 3: Configure API Settings in Odoo

### For Docker Setup:
If Odoo and API are in separate containers, use the container name or IP:
- **API Base URL**: `http://odoo_api:8000` (if using Docker network)
- **API Base URL**: `http://host.docker.internal:8000` (to access host from container)

### For Local Development:
- **API Base URL**: `http://localhost:8000`
- **Authentication URL**: `http://localhost:8000/api/v1/auth/token`
- **GraphQL URL**: `http://localhost:8000/graphql`

## Step 4: Test Authentication

Use the following credentials in your API configuration:
- **Username**: `admin` (or your actual username)
- **Password**: `admin` (or your actual password)

## Step 5: Alternative Configuration

If you're running Odoo in Docker but the API on host:

### Find your host IP:
```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
```

Then use: `http://<your_host_ip>:8000`

## Troubleshooting

### 1. Check if API is running:
```bash
docker ps | grep odoo_api
```

### 2. Check API logs:
```bash
cd odoo_api
docker-compose logs
```

### 3. Test API directly:
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=admin&password=admin"
```

### 4. If using Docker, check network:
```bash
docker network ls
docker network inspect <network_name>
```

## Common Issues

1. **Firewall blocking port 8000**
2. **Docker containers not on same network**
3. **API service crashed or not started**
4. **Wrong credentials in configuration**

## Quick Test

Once the API is running, you can test it with this Python script:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/token",
    data={"username": "admin", "password": "admin"}
)
print(response.json())
```

If this works, your Odoo module should also work.