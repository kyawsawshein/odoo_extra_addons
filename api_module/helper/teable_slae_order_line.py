# ============================================
# MODULE: Teable API - One-to-Many Relationships
# VERSION: v1.0.0
# DATE: 2026-03-26
# AUTHOR: Joe @ Zervi Azia
# PURPOSE: Handle Sale Order and Sale Order Line relationships
# TEABLE ORIGIN: Phase 2 - Mini Odoo ERP in Teable.ai
# ============================================

import requests
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

class TeableRelationshipClient:
    """
    Teable API Client for handling one-to-many relationships
    Specifically designed for Zervi Azia's Odoo migration project
    """
    
    def __init__(self, api_key: str, base_id: str):
        """
        Initialize Teable API client
        
        Args:
            api_key: Your Teable API key
            base_id: Your Teable base/workspace ID
        """
        self.api_key = api_key
        self.base_id = base_id
        self.base_url = "https://api.teable.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    # ============================================
    # METHOD 1: Using Link Field References
    # ============================================
    
    def get_sale_order_with_lines_via_link(self, order_id: str) -> Dict[str, Any]:
        """
        Get Sale Order with its lines using link field references
        
        In Teable, link fields store references as arrays of record IDs
        Example structure:
        - Sale Order table has field 'order_lines' (link to Sale Order Line table)
        - Sale Order Line table has field 'order_id' (link to Sale Order table)
        
        Args:
            order_id: Sale Order record ID
            
        Returns:
            Dictionary with order data and line items
        """
        try:
            # Step 1: Get the Sale Order record
            order_url = f"{self.base_url}/bases/{self.base_id}/tables/tblSaleOrder/records/{order_id}"
            order_params = {
                "fieldKeyType": "dbFieldName",
                "fields": "*"  # Get all fields including link fields
            }
            
            order_response = requests.get(order_url, headers=self.headers, params=order_params)
            order_response.raise_for_status()
            order_data = order_response.json()
            
            if not order_data:
                return {"error": "Sale Order not found"}
            
            # Step 2: Extract line IDs from the link field
            # In Teable, link fields are arrays of record IDs
            line_ids = order_data.get("fields", {}).get("order_lines", [])
            
            if not line_ids:
                return {
                    "order": order_data,
                    "lines": []
                }
            
            # Step 3: Get all line items
            lines = self._get_multiple_records("tblSaleOrderLine", line_ids)
            
            return {
                "order": order_data,
                "lines": lines
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting sale order with lines: {e}")
            return {"error": str(e)}
    
    def _get_multiple_records(self, table_id: str, record_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get multiple records by their IDs
        
        Args:
            table_id: Table ID
            record_ids: List of record IDs
            
        Returns:
            List of record dictionaries
        """
        try:
            # Teable might support batch GET or we need to fetch individually
            all_records = []
            
            for record_id in record_ids:
                url = f"{self.base_url}/bases/{self.base_id}/tables/{table_id}/records/{record_id}"
                params = {
                    "fieldKeyType": "dbFieldName",
                    "fields": "*"
                }
                
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                all_records.append(response.json())
            
            return all_records
            
        except Exception as e:
            print(f"Error getting multiple records: {e}")
            return []
    
    # ============================================
    # METHOD 2: Using Filter to Find Related Records
    # ============================================
    
    def get_sale_order_with_lines_via_filter(self, order_field: str, order_value: Any) -> Dict[str, Any]:
        """
        Get Sale Order with lines by filtering the lines table
        
        This method is useful when you don't have the order ID but have
        another unique field like order_number
        
        Args:
            order_field: Field name to search by (e.g., 'order_number')
            order_value: Value to search for
            
        Returns:
            Dictionary with order and lines
        """
        try:
            # Step 1: Find the Sale Order
            order = self._find_record_by_field("tblSaleOrder", order_field, order_value)
            
            if not order:
                return {"error": f"Sale Order with {order_field}={order_value} not found"}
            
            # Step 2: Find all lines for this order
            # Assuming Sale Order Line table has a field 'order_id' that links to Sale Order
            lines = self._find_records_by_field(
                table_id="tblSaleOrderLine",
                field_name="order_id",
                field_value=order["id"]
            )
            
            return {
                "order": order,
                "lines": lines
            }
            
        except Exception as e:
            print(f"Error getting sale order via filter: {e}")
            return {"error": str(e)}
    
    def _find_record_by_field(self, table_id: str, field_name: str, field_value: Any) -> Optional[Dict[str, Any]]:
        """Find a single record by field value"""
        try:
            url = f"{self.base_url}/bases/{self.base_id}/tables/{table_id}/records"
            
            # Build filter formula
            if isinstance(field_value, str):
                filter_formula = f"{{{field_name}}} = '{field_value}'"
            else:
                filter_formula = f"{{{field_name}}} = {field_value}"
            
            params = {
                "fieldKeyType": "dbFieldName",
                "filterByFormula": filter_formula,
                "limit": 1,
                "fields": "*"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            records = data.get("records", [])
            
            return records[0] if records else None
            
        except Exception as e:
            print(f"Error finding record by field: {e}")
            return None
    
    def _find_records_by_field(self, table_id: str, field_name: str, field_value: Any, 
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Find multiple records by field value"""
        try:
            url = f"{self.base_url}/bases/{self.base_id}/tables/{table_id}/records"
            
            # Build filter formula
            if isinstance(field_value, str):
                filter_formula = f"{{{field_name}}} = '{field_value}'"
            else:
                filter_formula = f"{{{field_name}}} = {field_value}"
            
            params = {
                "fieldKeyType": "dbFieldName",
                "filterByFormula": filter_formula,
                "limit": limit,
                "fields": "*"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("records", [])
            
        except Exception as e:
            print(f"Error finding records by field: {e}")
            return []
    
    # ============================================
    # METHOD 3: Batch Query with Expanded Fields
    # ============================================
    
    def get_sale_orders_with_lines_batch(self, order_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get multiple sale orders with their lines in batch
        
        Args:
            order_ids: List of sale order IDs
            
        Returns:
            List of orders with their lines
        """
        try:
            all_results = []
            
            for order_id in order_ids:
                result = self.get_sale_order_with_lines_via_link(order_id)
                if "error" not in result:
                    all_results.append(result)
            
            return all_results
            
        except Exception as e:
            print(f"Error in batch query: {e}")
            return []
    
    # ============================================
    # METHOD 4: Create Sale Order with Lines
    # ============================================
    
    def create_sale_order_with_lines(self, order_data: Dict[str, Any], 
                                    line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a Sale Order with its line items
        
        This simulates Odoo's sale.order creation with sale.order.line records
        
        Args:
            order_data: Sale Order fields
            line_items: List of line item dictionaries
            
        Returns:
            Created order with lines
        """
        try:
            # Step 1: Create the Sale Order
            order_id = self._create_record("tblSaleOrder", order_data)
            
            if not order_id:
                return {"error": "Failed to create Sale Order"}
            
            # Step 2: Create line items with reference to the order
            created_lines = []
            for line_item in line_items:
                # Add order reference to each line
                line_item["order_id"] = order_id
                
                line_id = self._create_record("tblSaleOrderLine", line_item)
                if line_id:
                    created_lines.append(line_id)
            
            # Step 3: Update the Sale Order with line references
            if created_lines:
                self._update_record("tblSaleOrder", order_id, {"order_lines": created_lines})
            
            # Step 4: Return the complete order with lines
            return self.get_sale_order_with_lines_via_link(order_id)
            
        except Exception as e:
            print(f"Error creating sale order with lines: {e}")
            return {"error": str(e)}
    
    def _create_record(self, table_id: str, fields: Dict[str, Any]) -> Optional[str]:
        """Create a single record"""
        try:
            url = f"{self.base_url}/bases/{self.base_id}/tables/{table_id}/records"
            
            payload = {
                "records": [{
                    "fields": fields
                }]
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data.get("records") and len(data["records"]) > 0:
                return data["records"][0]["id"]
            
            return None
            
        except Exception as e:
            print(f"Error creating record: {e}")
            return None
    
    def _update_record(self, table_id: str, record_id: str, fields: Dict[str, Any]) -> bool:
        """Update a single record"""
        try:
            url = f"{self.base_url}/bases/{self.base_id}/tables/{table_id}/records/{record_id}"
            
            payload = {
                "fieldKeyType": "dbFieldName",
                "fields": fields
            }
            
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            print(f"Error updating record: {e}")
            return False
    
    # ============================================
    # METHOD 5: Advanced Query with Field Expansion
    # ============================================
    
    def get_sale_order_expanded(self, order_id: str, expand_fields: List[str] = None) -> Dict[str, Any]:
        """
        Get Sale Order with expanded related fields
        
        This method attempts to expand related fields in a single query
        Note: Teable might not support field expansion like some APIs
        
        Args:
            order_id: Sale Order ID
            expand_fields: List of fields to expand (e.g., ['order_lines', 'customer_id'])
            
        Returns:
            Expanded order data
        """
        try:
            # Get the order with all fields
            order = self._get_record_by_id("tblSaleOrder", order_id)
            
            if not order:
                return {"error": "Order not found"}
            
            result = {"order": order}
            
            # Expand specified fields
            if expand_fields:
                for field in expand_fields:
                    if field in order.get("fields", {}):
                        field_value = order["fields"][field]
                        
                        # Handle link fields (arrays of IDs)
                        if isinstance(field_value, list):
                            # This is likely a link field
                            related_records = self._get_multiple_records_by_ids(field, field_value)
                            result[field] = related_records
                        else:
                            # Single reference
                            related_record = self._get_record_by_id(self._get_table_for_field(field), field_value)
                            result[field] = related_record
            
            return result
            
        except Exception as e:
            print(f"Error getting expanded order: {e}")
            return {"error": str(e)}
    
    def _get_record_by_id(self, table_id: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a single record by ID"""
        try:
            url = f"{self.base_url}/bases/{self.base_id}/tables/{table_id}/records/{record_id}"
            params = {
                "fieldKeyType": "dbFieldName",
                "fields": "*"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error getting record by ID: {e}")
            return None
    
    def _get_multiple_records_by_ids(self, field_name: str, record_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get multiple records by IDs for a specific field
        
        Args:
            field_name: Field name (used to determine table)
            record_ids: List of record IDs
            
        Returns:
            List of records
        """
        # Map field names to tables (you need to customize this)
        field_to_table = {
            "order_lines": "tblSaleOrderLine",
            "customer_id": "tblCustomer",
            "product_id": "tblProduct",
            "warehouse_id": "tblWarehouse"
        }
        
        table_id = field_to_table.get(field_name)
        if not table_id:
            return []
        
        return self._get_multiple_records(table_id, record_ids)
    
    def _get_table_for_field(self, field_name: str) -> str:
        """Map field name to table ID"""
        field_to_table = {
            "customer_id": "tblCustomer",
            "product_id": "tblProduct",
            "warehouse_id": "tblWarehouse",
            "salesperson_id": "tblEmployee"
        }
        return field_to_table.get(field_name, "")

# ============================================
# ZERVI AZIA SPECIFIC IMPLEMENTATION
# ============================================

class ZerviAziaSaleOrderManager:
    """
    Sale Order management specifically for Zervi Azia Thailand
    This class handles Thailand-specific business logic
    """
    
    def __init__(self, teable_client: TeableRelationshipClient):
        self.client = teable_client
    
    def get_thai_sale_order(self, order_number: str) -> Dict[str, Any]:
        """
        Get Sale Order with Thailand-specific formatting
        
        Args:
            order_number: Zervi Azia sale order number
            
        Returns:
            Formatted sale order with lines
        """
        try:
            # Get the order with lines
            result = self.client.get_sale_order_with_lines_via_filter(
                order_field="order_number",
                order_value=order_number
            )
            
            if "error" in result:
                return result
            
            # Add Thailand-specific calculations
            order = result["order"]
            lines = result["lines"]
            
            # Calculate Thailand VAT (7%)
            total_without_vat = sum(
                line.get("fields", {}).get("subtotal", 0) 
                for line in lines
            )
            
            vat_amount = total_without_vat * 0.07
            total_with_vat = total_without_vat + vat_amount
            
            # Format for Thailand
            formatted_result = {
                "order_number": order.get("fields", {}).get("order_number"),
                "customer": order.get("fields", {}).get("customer_name"),
                "order_date": order.get("fields", {}).get("order_date"),
                "delivery_date": order.get("fields", {}).get("delivery_date"),
                "status": order.get("fields", {}).get("status"),
                "thailand_specific": {
                    "vat_rate": 7.0,
                    "vat_amount": vat_amount,
                    "total_without_vat": total_without_vat,
                    "total_with_vat": total_with_vat,
                    "currency": "THB",
                    "tax_id": order.get("fields", {}).get("customer_tax_id", ""),
                    "branch_id": order.get("fields", {}).get("branch_id", "")
                },
                "line_items": [
                    {
                        "product_code": line.get("fields", {}).get("product_code"),
                        "product_name": line.get("fields", {}).get("product_name"),
                        "quantity": line.get("fields", {}).get("quantity"),
                        "unit_price": line.get("fields", {}).get("unit_price"),
                        "subtotal": line.get("fields", {}).get("subtotal"),
                        "vat_amount": line.get("fields", {}).get("subtotal", 0) * 0.07
                    }
                    for line in lines
                ]
            }
            
            return formatted_result
            
