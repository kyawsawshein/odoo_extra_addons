# ============================================
# MODULE: Teable API - One-to-Many Relationships
# VERSION: v1.0.0
# DATE: 2026-03-26
# AUTHOR: Joe @ Zervi Azia
# PURPOSE: Handle Sale Order and Sale Order Line relationships
# TEABLE ORIGIN: Phase 2 - Mini Odoo ERP in Teable.ai
# ============================================

import json
import logging
from datetime import datetime
from encodings.punycode import T
from typing import Any, Dict, List, Optional

import requests

from .teable_endpoint import Method, TeableAPIClient

_logger = logging.getLogger(__name__)


class TeableSaleOrderAPI(TeableAPIClient):
    """
    Teable API Client for handling one-to-many relationships
    Specifically designed for Zervi Azia's Odoo migration project
    """

    def get_sale_order_sql(self) -> str:
        return f"""
            SELECT so."__id","Customer", p."partner_id", "Status","Order_Date","Delivery_Date","PO_No","Source_Location","Company","Sale_Team","Name","Sales_Order_Lines"
            FROM "{self.database}"."Sales_Orders" so
                LEFT JOIN "{self.database}"."Partners" p ON  (so."Customer"->>'id') = p."__id"
            WHERE "Status" = 'Confirmed' AND "Name" = 'SO-16'
        """

    def get_sale_order_lines_sql(self) -> str:
        return f"""
            SELECT sol."__id",sol."default_code","Qty","Unit_Price","Job_No", p."id" as product_id, uom."uom_id"
            FROM "{self.database}"."Sales_Order_Lines" sol
                LEFT JOIN "{self.database}"."Products" p ON (sol."default_code"->>'id') = p."__id"
                LEFT JOIN "{self.database}"."Units_of_Measure" uom ON (p."uom_id"->>'id') = uom."__id"
            WHERE sol."__id" IN ($line_ids)
        """

    def get_sale_order(self) -> List:
        sale_order = []
        orders = self.execute_sql_query(sql=self.get_sale_order_sql())
        for order in orders.get("rows", []):
            line_ids = [l["id"] for l in order.get("Sales_Order_Lines", [])]
            if not line_ids:
                sale_order.append({"order": order, "lines": []})
            lines = self.execute_sql_query(
                sql=self.get_sale_order_lines_sql().replace(
                    "$line_ids", ",".join([f"'{i}'" for i in line_ids])
                )
            )
            sale_order.append({"order": order, "lines": lines})
        return sale_order
