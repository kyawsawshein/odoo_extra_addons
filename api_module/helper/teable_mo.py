import json
import logging
from datetime import datetime
from encodings.punycode import T
from typing import Any, Dict, List, Optional

import requests

from .teable_endpoint import Method, TeableAPIClient

_logger = logging.getLogger(__name__)


class TeableManufactureAPI(TeableAPIClient):
    """
    Teable API Client for handling one-to-many relationships
    Specifically designed for Zervi Azia's Odoo migration project
    """

    def get_manufacture_orders_sql(self) -> str:
        return f"""
            SELECT "__id","Product", "Quantity", "Production_Raw_Material", "Finished_Goods"
            FROM "{self.database}"."MO"
            WHERE "Status" = 'Done' AND "Name" = 'MO-3'
        """

    def get_mo_raw_material_lines_sql(self) -> str:
        return f"""
            SELECT p."id" as product_id, p."default_code", raw."Consume_Qty", raw."Lot_ids", uom."uom_id", raw."Total_Cost"
            FROM "{self.database}"."MO_Raw_Material" raw
                LEFT JOIN "{self.database}"."Products" p ON (raw."Product"->>'id') = p."__id"
                LEFT JOIN "{self.database}"."Units_of_Measure" uom ON (p."uom_id"->>'id') = uom."__id"
            WHERE raw."__id" IN ($raw_ids)
        """

    def get_mo_finished_goods_lines_sql(self) -> str:
        return f"""
            SELECT p."id" as product_id,p."default_code",fgo."Finished_Qty",fgo."Cost", uom."uom_id", fgo."Lot_No"
            FROM "{self.database}"."MO_Finished_Goods" fgo
                LEFT JOIN "{self.database}"."Products" p ON (fgo."Product"->>'id') = p."__id"
                LEFT JOIN "{self.database}"."Units_of_Measure" uom ON (p."uom_id"->>'id') = uom."__id"
            WHERE fgo."__id" IN ($goods_ids)
        """

    def get_manufacture_orders(self) -> List:
        manufacture_orders = []
        mo_orders = self.execute_sql_query(sql=self.get_manufacture_orders_sql())
        for order in mo_orders.get("rows", []):
            raw_line_ids = [l["id"] for l in order.get("Production_Raw_Material", [])]
            goods_line_ids = [l["id"] for l in order.get("Finished_Goods", [])]
            if not raw_line_ids:
                manufacture_orders.append({"order": order, "raw_lines": []})
            raw_lines = self.execute_sql_query(
                sql=self.get_mo_raw_material_lines_sql().replace(
                    "$raw_ids", ",".join([f"'{i}'" for i in raw_line_ids])
                )
            )
            if not goods_line_ids:
                manufacture_orders.append({"order": order, "goods_lines": []})
            goods_lines = self.execute_sql_query(
                sql=self.get_mo_finished_goods_lines_sql().replace(
                    "$goods_ids", ",".join([f"'{i}'" for i in goods_line_ids])
                )
            )
            manufacture_orders.append(
                {
                    "order": order.get("row", {}),
                    "raw_lines": raw_lines.get("rows", []),
                    "goods_lines": goods_lines.get("rows", []),
                }
            )
        return manufacture_orders
