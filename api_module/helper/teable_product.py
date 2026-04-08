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


class TeableProductAPI(TeableAPIClient):
    """
    Teable API Client for handling one-to-many relationships
    Specifically designed for Zervi Azia's Odoo migration project
    """

    def get_products_sql(self) -> str:
        return f"""
            SELECT "__id" As "id", "default_code", "name", "barcode", "categ_id", "standard_price", "list_price", "qty_available", "uom_id", "write_date"
            FROM "{self.database}"."Products"
            WHERE "default_code" IN ($codes)
        """

    def get_sale_order_lines_sql(self) -> str:
        return f"""
            SELECT sol."__id",sol."default_code","Qty","Unit_Price","Job_No", p."id" as product_id, uom."uom_id"
            FROM "{self.database}"."Sales_Order_Lines" sol
                LEFT JOIN "{self.database}"."Products" p ON (sol."default_code"->>'id') = p."__id"
                LEFT JOIN "{self.database}"."Units_of_Measure" uom ON (p."uom_id"->>'id') = uom."__id"
            WHERE sol."__id" IN ($line_ids)
        """

    def get_products(self, codes: List[str]) -> List[Dict]:
        product_dict = {}
        sql = self.get_products_sql().replace(
            "$codes", ",".join([f"'{code}'" for code in codes])
        )
        products = self.execute_sql_query(sql=sql)
        for product in products.get("rows", []):
            product_dict[product["default_code"]] = product
        return list(product_dict.values())
