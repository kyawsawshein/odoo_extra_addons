"""
Test script demonstrating how to use the API module endpoints
This matches the user's JavaScript example for syncing products by lot
"""

import requests
import json

# Configuration - Update these with your Odoo instance details
ODOO_URL = "http://localhost:8069"
API_BASE_URL = f"{ODOO_URL}/api/v1"
API_KEY = "your-api-key-here"  # Or use JWT token

# Example 1: Using the comprehensive sync endpoint (matches JavaScript example)
def test_sync_product_by_lot():
    """Test the sync_product_by_lot endpoint that matches the JavaScript example"""
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,  # Or use 'Authorization': 'Bearer <jwt_token>'
    }
    
    payload = {
        "part_no": "TEST-PART-001",
        "product_code": "TEST-PROD-001",
        "qty": 100,
        "unit": "Units",
        "lot_no": "TEST-LOT-001",
        "status": "done"
    }
    
    print("=== Testing sync_product_by_lot endpoint ===")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/sync/product_by_lot",
            headers=headers,
            json=payload
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200 and response.json().get('success'):
            print("✅ Sync successful!")
            data = response.json()['data']
            print(f"   Product ID: {data.get('product_id')}")
            print(f"   Lot ID: {data.get('lot_id')}")
            print(f"   Part No: {data.get('part_no')}")
            print(f"   Quantity: {data.get('qty')}")
        else:
            print("❌ Sync failed")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# Example 2: Using individual endpoints
def test_individual_endpoints():
    """Test individual API endpoints"""
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
    }
    
    print("\n=== Testing individual endpoints ===")
    
    # 1. Create product
    product_payload = {
        "name": "API Test Product",
        "default_code": "API-TEST-001",
        "type": "product",
        "tracking": "lot",
        "list_price": 99.99,
        "standard_price": 79.99
    }
    
    print("\n1. Creating product...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/products/create",
            headers=headers,
            json=product_payload
        )
        print(f"   Response: {response.status_code}")
        if response.status_code == 200:
            print(f"   Product created: {response.json()}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    # 2. Search or create product (like in JavaScript example)
    search_payload = {
        "name": "Test Product",
        "default_code": "TEST-001",
        "unit": "Units"
    }
    
    print("\n2. Searching or creating product...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/products/search_or_create",
            headers=headers,
            json=search_payload
        )
        print(f"   Response: {response.status_code}")
        if response.status_code == 200:
            print(f"   Result: {response.json()}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    # 3. Create stock quant by lot
    quant_payload = {
        "product_id": 1,  # Replace with actual product ID
        "lot_id": 1,      # Replace with actual lot ID
        "qty": 50,
        "location_id": 8  # Default stock location
    }
    
    print("\n3. Creating stock quant by lot...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/stock/quant/by_lot",
            headers=headers,
            json=quant_payload
        )
        print(f"   Response: {response.status_code}")
        if response.status_code == 200:
            print(f"   Result: {response.json()}")
    except Exception as e:
        print(f"   Error: {str(e)}")

# Example 3: Authentication test
def test_authentication():
    """Test JWT authentication"""
    
    print("\n=== Testing JWT Authentication ===")
    
    # Get JWT token
    auth_payload = {
        "login": "admin",
        "password": "admin"
    }
    
    try:
        response = requests.post(
            f"{ODOO_URL}/jwt/login",
            headers={'Content-Type': 'application/json'},
            json=auth_payload
        )
        
        if response.status_code == 200:
            token = response.json()[0]['token']
            print(f"✅ JWT Token obtained: {token[:50]}...")
            
            # Use token for API call
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            
            test_payload = {
                "part_no": "JWT-TEST",
                "product_code": "JWT-001",
                "qty": 10,
                "unit": "Units",
                "lot_no": "JWT-LOT-001",
                "status": "done"
            }
            
            response = requests.post(
                f"{API_BASE_URL}/sync/product_by_lot",
                headers=headers,
                json=test_payload
            )
            
            print(f"   API call with JWT: {response.status_code}")
            if response.status_code == 200:
                print(f"   Result: {response.json().get('message')}")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# API Endpoints Documentation
def print_api_documentation():
    """Print available API endpoints"""
    
    print("\n" + "="*60)
    print("API MODULE ENDPOINTS DOCUMENTATION")
    print("="*60)
    
    endpoints = [
        ("POST /api/v1/products/create", "Create a new product"),
        ("POST /api/v1/products/search_or_create", "Search or create product (matches JavaScript logic)"),
        ("POST /api/v1/stock/moves/create", "Create a stock move"),
        ("POST /api/v1/mrp/production/create", "Create a manufacturing order"),
        ("POST /api/v1/stock/quant/by_lot", "Create or update stock quant by lot"),
        ("POST /api/v1/sync/product_by_lot", "Comprehensive sync (matches JavaScript example)"),
        ("POST /jwt/login", "Get JWT token (JSON: {'login': '...', 'password': '...'})"),
        ("POST /jwt/call", "Generic JWT RPC call"),
    ]
    
    for endpoint, description in endpoints:
        print(f"{endpoint:40} - {description}")
    
    print("\n" + "="*60)
    print("AUTHENTICATION METHODS:")
    print("1. API Key: Add 'X-API-Key: <your-api-key>' header")
    print("2. JWT Token: Add 'Authorization: Bearer <jwt-token>' header")
    print("="*60)

if __name__ == "__main__":
    print_api_documentation()
    
    print("\nTo run tests, update the configuration variables at the top of this file:")
    print("1. Set ODOO_URL to your Odoo instance URL")
    print("2. Set API_KEY to a valid API key or use JWT authentication")
    print("\nUncomment the test functions below to run them:")
    print("# test_sync_product_by_lot()")
    print("# test_individual_endpoints()")
    print("# test_authentication()")