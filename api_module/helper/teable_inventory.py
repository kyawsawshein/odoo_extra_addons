import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

# from ..datamodels.datamodel import Method
from .teable_endpoint import TeableAPIClient

_logger = logging.getLogger(__name__)


class Method:
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"


class TeableInventory(TeableAPIClient):
    """Complete Teable API client for Zervi Azia ERP"""

    def update_record_by_id(
        self, table: str, record_id: str, update_fields: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a record by its ID
        Args:
            table: The ID of the table
            record_id: The ID of the record to update
            update_fields: Dictionary of field names and new values

        Returns:
            Updated record dictionary, or None if failed
        """
        try:
            endpoint = self.get_endpoint(table, record_id=record_id)
            # Prepare update payload
            payload = {
                "fieldKeyType": "dbFieldName",
                "record": {"fields": update_fields},
            }
            # PATCH method for partial update
            return self._make_request(Method.PATCH, endpoint=endpoint, params=payload)

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error updating record by ID: {e}")
            return None

    def find_record_by_field(
        self, table: str, field_name: str, field_value: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Find a record by field value
        Equivalent SQL: SELECT * FROM table WHERE field_name = field_value LIMIT 1

        Args:
            table: The ID of the table to query
            field_name: The field name to search by
            field_value: The value to search for

        Returns:
            Dictionary containing the record, or None if not found
        """
        try:
            filter_value = [
                {"fieldId": "id", "operator": "is", "value": 6},
            ]
            sort_value = [{"fieldId": "id", "order": "asc"}]
            params = {
                "fieldKeyType": "dbFieldName",
                "filter": json.dumps(
                    {
                        "conjunction": "and",
                        "filterSet": filter_value,
                    }
                ),
                "orderBy": json.dumps(sort_value),
                "cellFormat": "json",
                "limit": 3,
                "fields": "*",
            }

            endpoint = self.get_endpoint(table)
            data = self._make_request(Method.GET, endpoint=endpoint, params=params)
            print(data)
            if data.get("records") and len(data["records"]) > 0:
                return data["records"][0]
            else:
                print(f"No record found with {field_name} = {field_value}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error finding record by field: {e}")
            return None

    def get_max_write_date_record(
        self, table: str, date_field: str = "write_date"
    ) -> Optional[Dict[str, Any]]:
        """
        Get the record with the maximum write_date from a table
        Equivalent SQL: SELECT * FROM table ORDER BY write_date DESC LIMIT 1
        Args:
            table: The ID of the table to query
            date_field: The field name containing the date (default: "write_date")
        Returns:
            Dictionary containing the record with maximum write_date, or None if no records
        """
        try:
            # Build the URL for the records endpoint
            endpoint = self.get_endpoint(table)
            # Query parameters: sort by write_date descending, limit to 1 record
            params = {
                "fieldKeyType": "dbFieldName",
                "cellFormat": "json",
                "orderBy": json.dumps([{"fieldId": date_field, "order": "desc"}]),
                "pageSize": 1,
                "page": 1,
                "fields": "*",  # Get all fields
            }
            _logger.info("Params %s ", params)
            result = self._make_request(
                method=Method.GET, endpoint=endpoint, params=params
            )
            _logger.info("result : %s ", result)
            if result and result.get("records") and len(result["records"]) > 0:
                return result["records"][0]
            else:
                print(f"No records found in table {table}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching max write_date record: {e}")
            return None

    def get_max_write_date_value(
        self, table: str, date_field: str = "write_date"
    ) -> Optional[str]:
        """
        Get only the maximum write_date value from a table
        Equivalent SQL: SELECT MAX(write_date) FROM table
        Args:
            table: The ID of the table to query
            date_field: The field name containing the date (default: "write_date")
        Returns:
            String containing the maximum write_date value, or None if no records
        """
        record = self.get_max_write_date_record(table, date_field)
        if record and "fields" in record:
            return record["fields"].get(date_field)
        return None

    def get_records_after_date(
        self, table: str, date_field: str, after_date: str, limit: int = 100
    ) -> list:
        """
        Get records created/modified after a specific date
        Equivalent SQL: SELECT * FROM table WHERE write_date > 'date' ORDER BY write_date
        Args:
            table: The ID of the table to query
            date_field: The field name containing the date
            after_date: ISO format date string (e.g., "2024-01-01T00:00:00Z")
            limit: Maximum number of records to return
        Returns:
            List of records after the specified date
        """
        try:
            # Filter formula: date_field > after_date
            # Note: Teable uses formulas similar to Airtable
            filter_formula = f"{{{date_field}}} > '{after_date}'"
            params = {
                "filterByFormula": filter_formula,
                "sort": date_field,  # Ascending order
                "limit": limit,
                "fields": "*",
            }
            endpoint = self.get_endpoint(table)
            result = self._make_request(Method.GET, endpoint, params=params)
            return result.get("records", [])

        except requests.exceptions.RequestException as e:
            print(f"Error fetching records after date: {e}")
            return []


client = TeableInventory(
    database="bse0fQ6EXNGdiMURvQs",
    api_token="teable_acc65mmZVTtEo9VcPja_M/ACnbw8UHoLtGX6HW52TYUgUArZegSjHQ3MTvNecwE=",
    base_url="https://teable-team-zervi-u34072.vm.elestio.app/api",
)


uom = client.get_records(table='uom')
print(uom)
