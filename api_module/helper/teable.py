# ============================================
# MODULE: teable_api_create.py
# VERSION: v1.0.0
# DATE: 2026-03-24
# AUTHOR: Joe @ Zervi Azia
# PURPOSE: Create records in Teable.ai tables
# TEABLE ORIGIN: Stock_Move table
# ============================================

import requests
import json
from datetime import datetime

class TeableAPI:
    def __init__(self, api_token, base_url="https://teable-team-zervi-u34072.vm.elestio.app"):
        """
        Initialize Teable API client
        
        Args:
            api_token (str): Your Teable API token
            base_url (str): Teable instance URL
        """
        self.api_token = api_token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def create_record(self, table_id, record_data, field_key_type="name"):
        """
        Create a new record in Teable table
        
        Args:
            table_id (str): Table ID (e.g., "tbl9aSJM516XzNYpTSa")
            record_data (dict): Record data with field names as keys
            field_key_type (str): "name" or "id" for field references
        
        Returns:
            dict: API response
        """
        url = f"{self.base_url}/table/{table_id}/record"
        
        payload = {
            "fieldKeyType": field_key_type,
            "records": [
                {
                    "fields": record_data
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating record: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return None

# ============================================
# EXAMPLE USAGE: Create Stock_Move Record
# ============================================

def create_stock_move_example():
    """Example: Create a stock movement record"""
    
    # Initialize API client
    api = TeableAPI(api_token="_YOUR_API_TOKEN_")
    
    # Table ID for Stock_Move table
    STOCK_MOVE_TABLE_ID = "tbl9aSJM516XzNYpTSa"  # Replace with actual table ID
    
    # Sample stock movement data
    stock_move_data = {
        "Product": "Product A",  # Product reference
        "MO": "MO-001",  # Manufacturing Order reference
        "Quantity": 100.0,
        "Source Location": "Warehouse A",
        "Destination Location": "Production Line 1",
        "BOM Line": "BOM-LINE-001",
        "Lot": "LOT-2024-001",
        "Created By": "Joe",
        "Created At": datetime.now().isoformat(),
        "Product Cost": 25.50,
        "Scrap Rate": 0.05,
        "Lead Time": 3,
        "Scrap Percent": 2.5,
        "Unit": "pcs",
        "Used Qty": 95.0,
        "Width": 120.0,
        "Minimum Order Qty": 50.0,
        "Stock Onhand": 500.0,
        "Raw Unit": "meters",
        "Stock Move": "IN"  # IN/OUT/TRANSFER
    }
    
    # Create the record
    result = api.create_record(
        table_id=STOCK_MOVE_TABLE_ID,
        record_data=stock_move_data,
        field_key_type="name"
    )
    
    if result:
        print("✅ Record created successfully!")
        print(f"Record ID: {result.get('records', [{}])[0].get('id')}")
        print(f"Full response: {json.dumps(result, indent=2)}")
    else:
        print("❌ Failed to create record")
    
    return result

# ============================================
# BATCH CREATE RECORDS
# ============================================

def create_multiple_records():
    """Create multiple records in batch"""
    
    api = TeableAPI(api_token="_YOUR_API_TOKEN_")
    TABLE_ID = "tbl9aSJM516XzNYpTSa"
    
    # Multiple stock movements
    batch_records = [
        {
            "Product": "Product A",
            "Quantity": 50,
            "Source Location": "Supplier",
            "Destination Location": "Warehouse",
            "Stock Move": "IN",
            "Created By": "Joe"
        },
        {
            "Product": "Product B", 
            "Quantity": 30,
            "Source Location": "Warehouse",
            "Destination Location": "Production",
            "Stock Move": "OUT",
            "Created By": "Joe"
        },
        {
            "Product": "Product C",
            "Quantity": 20,
            "Source Location": "Production",
            "Destination Location": "Quality Control",
            "Stock Move": "TRANSFER",
            "Created By": "Joe"
        }
    ]
    
    results = []
    for record_data in batch_records:
        result = api.create_record(TABLE_ID, record_data)
        if result:
            results.append(result)
            print(f"✅ Created record for {record_data['Product']}")
        else:
            print(f"❌ Failed to create record for {record_data['Product']}")
    
    return results

# ============================================
# CREATE WITH VALIDATION
# ============================================

def create_record_with_validation():
    """Create record with data validation"""
    
    api = TeableAPI(api_token="_YOUR_API_TOKEN_")
    TABLE_ID = "tbl9aSJM516XzNYpTSa"
    
    def validate_stock_move_data(data):
        """Validate stock movement data"""
        errors = []
        
        # Required fields
        required_fields = ["Product", "Quantity", "Stock Move"]
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Quantity validation
        if "Quantity" in data and data["Quantity"] <= 0:
            errors.append("Quantity must be greater than 0")
        
        # Stock Move validation
        valid_moves = ["IN", "OUT", "TRANSFER"]
        if "Stock Move" in data and data["Stock Move"] not in valid_moves:
            errors.append(f"Stock Move must be one of: {', '.join(valid_moves)}")
        
        return errors
    
    # Test data
    test_data = {
        "Product": "Test Product",
        "Quantity": 100,
        "Stock Move": "IN",
        "Created By": "Joe"
    }
    
    # Validate before creating
    validation_errors = validate_stock_move_data(test_data)
    
    if validation_errors:
        print("❌ Validation errors:")
        for error in validation_errors:
            print(f"  - {error}")
        return None
    
    # Create if validation passes
    result = api.create_record(TABLE_ID, test_data)
    
    if result:
        print("✅ Record created with validation")
    else:
        print("❌ Failed to create record")
    
    return result

# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("TEABLE.AI API - CREATE RECORDS")
    print("=" * 50)
    
    # Replace with your actual API token
    API_TOKEN = "_YOUR_API_TOKEN_"
    
    # Example 1: Single record creation
    print("\n1. Creating single stock move record...")
    create_stock_move_example()
    
    # Example 2: Batch creation
    print("\n2. Creating multiple records...")
    create_multiple_records()
    
    # Example 3: Create with validation
    print("\n3. Creating record with validation...")
    create_record_with_validation()
