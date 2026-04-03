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

    def get_order_with_lines_via_link(
        self, raw_table_id: str, goods_table_id: str, order_data: Dict
    ) -> Dict[str, Any]:
        raw_ids = order_data.get("fields", {}).get("Production_Raw_Material", [])
        raw_lines = self._get_multiple_records(raw_table_id, raw_ids)

        goods_ids = order_data.get("fields", {}).get("Finished_Goods", [])
        goods_lines = self._get_multiple_records(goods_table_id, goods_ids)

        return {"order": order_data, "raw_lines": raw_lines, "goods_lines": goods_lines}

    def _get_multiple_records(self, table_id: str, record_ids: List[str]) -> List[Dict]:
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
            params = self.get_params()
            for record in record_ids:
                endpoint = self.get_endpoint(table_id, record.get("id"))
                response = self._make_request(
                    method=Method.GET, endpoint=endpoint, params=params
                )
                all_records.append(response)
            return all_records
        except Exception as e:
            print(f"Error getting multiple records: {e}")
            return []

    # ============================================
    # METHOD 3: Batch Query with Expanded Fields
    # ============================================
    def get_orders_with_lines_batch(
        self, table_id: str, line_table_id: str, order_ids: List[str]
    ) -> List[Dict[str, Any]]:
        try:
            all_results = []
            for order_id in order_ids:
                result = self.get_order_with_lines_via_link(
                    table_id, line_table_id, order_id
                )
                if "error" not in result:
                    all_results.append(result)

            return all_results

        except Exception as e:
            print(f"Error in batch query: {e}")
            return []
