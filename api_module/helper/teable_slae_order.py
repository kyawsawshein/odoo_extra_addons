# ============================================
# MODULE: Teable API - One-to-Many Relationships
# VERSION: v1.0.0
# DATE: 2026-03-26
# AUTHOR: Joe @ Zervi Azia
# PURPOSE: Handle Sale Order and Sale Order Line relationships
# TEABLE ORIGIN: Phase 2 - Mini Odoo ERP in Teable.ai
# ============================================

from encodings.punycode import T

import requests
import json
from typing import Optional, Dict, Any, List
from datetime import datetime


from .teable_endpoint import TeableAPIClient
from .teable_endpoint import Method


class TeableSaleOrderAPI(TeableAPIClient):
    """
    Teable API Client for handling one-to-many relationships
    Specifically designed for Zervi Azia's Odoo migration project
    """

    # ============================================
    # METHOD 1: Using Link Field References
    # ============================================

    def get_sale_order_with_lines_via_link(
        self, table_id: str, order_id: str
    ) -> Dict[str, Any]:
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
            params = {
                "fieldKeyType": "dbFieldName",
                "fields": "*",  # Get all fields including link fields
            }
            endpoint = self.get_endpoint(table_id=table_id, record_id=order_id)
            order_data = self._make_request(
                method=Method.GET, endpoint=endpoint, json=params
            )

            if not order_data:
                return {"error": "Sale Order not found"}

            # Step 2: Extract line IDs from the link field
            # In Teable, link fields are arrays of record IDs
            line_ids = order_data.get("fields", {}).get("order_lines", [])
            line_table_id = "tblSaleOrderLine"
            if not line_ids:
                return {"order": order_data, "lines": []}
            
            # Step 3: Get all line items
            lines = self._get_multiple_records(line_table_id, line_ids)

            return {"order": order_data, "lines": lines}

        except requests.exceptions.RequestException as e:
            print(f"Error getting sale order with lines: {e}")
            return {"error": str(e)}

    def _get_multiple_records(
        self, table_id: str, record_ids: List[str]
    ) -> List[Dict[str, Any]]:
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
                endpoint = self.get_endpoint(table_id, record_id)
                params = {"fieldKeyType": "dbFieldName", "fields": "*"}
                response = self._make_request(
                    method=Method.GET, endpoint=endpoint, json=params
                )
                all_records.append(response)
            return all_records

        except Exception as e:
            print(f"Error getting multiple records: {e}")
            return []

    # ============================================
    # METHOD 2: Using Filter to Find Related Records
    # ============================================

    def get_sale_order_with_lines_via_filter(
        self, order_field: str, order_value: Any
    ) -> Dict[str, Any]:
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
            order = self.find_record_by_field("tblSaleOrder", order_field, order_value)

            if not order:
                return {
                    "error": f"Sale Order with {order_field}={order_value} not found"
                }

            # Step 2: Find all lines for this order
            # Assuming Sale Order Line table has a field 'order_id' that links to Sale Order
            lines = self.find_record_by_field(
                table_id="tblSaleOrderLine",
                field_name="order_id",
                field_value=order["id"],
            )

            return {"order": order, "lines": lines}

        except Exception as e:
            print(f"Error getting sale order via filter: {e}")
            return {"error": str(e)}

    # ============================================
    # METHOD 3: Batch Query with Expanded Fields
    # ============================================

    def get_sale_orders_with_lines_batch(
        self, table_id: str, line_table_id: str, order_ids: List[str]
    ) -> List[Dict[str, Any]]:
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
                result = self.get_sale_order_with_lines_via_link(table_id, order_id)
                if "error" not in result:
                    all_results.append(result)

            return all_results

        except Exception as e:
            print(f"Error in batch query: {e}")
            return []

    # ============================================
    # METHOD 4: Create Sale Order with Lines
    # ============================================

    def create_sale_order_with_lines(
        self, table_id: str, order_data: Dict[str, Any], line_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
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
            order_id = self.create_record(table_id, order_data)

            if not order_id:
                return {"error": "Failed to create Sale Order"}

            # Step 2: Create line items with reference to the order
            created_lines = []
            line_table_id = "tblSaleOrderLine"
            for line_item in line_items:
                # Add order reference to each line
                line_item["order_id"] = order_id

                line_id = self.create_record(line_table_id, line_item)
                if line_id:
                    created_lines.append(line_id)

            # Step 3: Update the Sale Order with line references
            if created_lines:
                self.update_record(table_id, order_id.get("id"), {"order_lines": created_lines})

            # Step 4: Return the complete order with lines
            return self.get_sale_order_with_lines_via_link(order_id)

        except Exception as e:
            print(f"Error creating sale order with lines: {e}")
            return {"error": str(e)}

    # ============================================
    # METHOD 5: Advanced Query with Field Expansion
    # ============================================

    def _get_record_by_id(self, table_id: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a single record by ID"""
        endpoint = self.get_endpoint(table_id, record_id=record_id)
        params = {
            "fieldKeyType": "dbFieldName",
            "fields": "*"
        }
        return self._make_request(Method.GET, endpoint=endpoint, json=params)

    def get_sale_order_expanded(
        self, table_id: str,order_id: str, expand_fields: List[str] = None
    ) -> Dict[str, Any]:
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
            order = self._get_record_by_id(table_id, order_id)
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
                            related_records = self._get_multiple_records_by_ids(
                                field, field_value
                            )
                            result[field] = related_records
                        else:
                            # Single reference
                            related_record = self._get_record_by_id(table_id, field_value)
                            result[field] = related_record

            return result

        except Exception as e:
            print(f"Error getting expanded order: {e}")
            return {"error": str(e)}

    def _get_multiple_records_by_ids(
        self, field_name: str, record_ids: List[str]
    ) -> List[Dict[str, Any]]:
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
            "warehouse_id": "tblWarehouse",
        }

        table_id = field_to_table.get(field_name)
        if not table_id:
            return []

        return self._get_multiple_records(table_id, record_ids)
