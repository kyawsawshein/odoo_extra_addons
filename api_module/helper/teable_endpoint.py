import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

# from ..datamodels.datamodel import Method

_logger = logging.getLogger(__name__)


class Method:
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"


class TeableAPIClient:
    """Complete Teable API client for Zervi Azia ERP"""

    def __init__(self, database: str, api_token: str, base_url: str = None):
        """
        Initialize Teable API client
        Args:
            api_token: Your Teable API token
            base_url: Teable instance URL (default: Zervi Azia instance)
        """
        self.database = database
        self.api_token = api_token
        self.base_url = base_url or (
            "https://teable-team-zervi-u34072.vm.elestio.app/api"
        )

        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        _logger.info("Teable AI Connected...")

    def execute_sql_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute SQL-like query on Teable

        Note: Teable might have SQL endpoint or use different API
        This is a placeholder - you need to check Teable's actual SQL API
        """
        try:
            # This URL might be different - check Teable documentation

            url = f"https://teable-team-zervi-u34072.vm.elestio.app/v1/bases/{self.database}/query"
            payload = {"query": sql, "parameters": {}}

            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json().get("records", [])

        except Exception as e:
            _logger.info(f"SQL query failed: {e}")
            # Fall back to REST API
            return []

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request to Teable API"""
        url = f"{self.base_url}{endpoint}"
        _logger.info("Teable URL : %s", url)
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error(f"API Error: {e}")
            if hasattr(e, "response") and e.response is not None:
                _logger.error(f"Response: {e.response.text}")
            return None

    def strategy_field_max_sql(self, table_id: str, date_field: str) -> Optional[str]:
        """Strategy 3: SQL query (if supported)"""
        try:
            sql = f"SELECT MAX({date_field}) as max_date FROM {table_id}"
            results = self.execute_sql_query(sql)

            if results and results[0].get("max_date"):
                return results[0]["max_date"]

        except Exception as e:
            print(f"Strategy 3 (SQL) failed: {e}")

        return None

    # ========== CRUD OPERATIONS ==========
    def get_endpoint_query(self, table_id: str, record_id: str = None):
        endpoint = f"/table/{table_id}/record"
        if record_id:
            endpoint = f"/table/{table_id}/record/{record_id}"

        return endpoint

    def get_endpoint(self, table_id: str, record_id: str = None):
        endpoint = f"/table/{table_id}/record"
        if record_id:
            endpoint = f"/table/{table_id}/record/{record_id}"

        return endpoint

    def get_payload(self, fields: Dict):
        payload = {"fieldKeyType": "dbFieldName", "record": {"fields": fields}}
        return payload

    def create_record(
        self, table_id: str, fields: Dict, field_key_type: str = "dbFieldName"
    ) -> Optional[Dict]:
        """
        Create a single record
        Args:
            table: Table ID
            fields: Field data dictionary
            field_key_type: "name" or "id"
        Returns:
            Created record data
        """
        endpoint = self.get_endpoint(table_id)
        payload = {"fieldKeyType": field_key_type, "records": [{"fields": fields}]}
        _logger.info("Create record payload : %s ", payload)
        return self._make_request(Method.POST, endpoint, json=payload)

    def create_batch_records(
        self, table_id: str, records: List[Dict], field_key_type: str = "dbFieldName"
    ) -> Optional[Dict]:
        """
        Create multiple records in batch
        Args:
            table: Table ID
            records: List of field data dictionaries
            field_key_type: "name" or "id"
        Returns:
            Batch creation result
        """
        endpoint = self.get_endpoint(table_id)
        payload = {
            "fieldKeyType": field_key_type,
            "records": [{"fields": record} for record in records],
        }
        return self._make_request(Method.POST, endpoint, params=payload)

    def get_records(
        self,
        table_id: str,
        filter_list: Optional[List] = None,
        sort_list: Any = None,
        **params,
    ) -> Optional[Dict]:
        """
        Get records from table
        Args:
            table: Table ID
            filter_list:  [{"fieldId": "Status", "operator": "is", "value": "Done"}]
            sort_list: [{"fieldId": field_name, "order": "asc"}]
            **params: Additional query parameters
        Returns:
            Records data
        """
        endpoint = self.get_endpoint(table_id)
        query_params = {
            "fieldKeyType": "dbFieldName",
            "cellFormat": "json",
            **params,
        }
        if filter_list:
            query_params["filter"] = json.dumps(
                {
                    "conjunction": "and",
                    "filterSet": filter_list,
                }
            )
        if sort_list:
            query_params["orderBy"] = (json.dumps(sort_list),)
        _logger.info("#Get record params : %s", query_params)
        response = self._make_request(Method.GET, endpoint, params=query_params)
        _logger.info("#Get record response : %s ", response)
        return response.get("records")

    def update_record(
        self,
        table_id: str,
        record_id: str,
        fields: Dict,
        field_key_type: str = "dbFieldName",
    ) -> Optional[List]:
        """
        Update a record
        Args:
            table: Table ID
            record_id: Record ID to update
            fields: Updated field data
            field_key_type: "name" or "id"
        Returns:
            Updated record data
        """
        endpoint = self.get_endpoint(table_id, record_id=record_id)
        payload = {"fieldKeyType": field_key_type, "record": {"fields": fields}}
        return self._make_request(Method.PATCH, endpoint=endpoint, json=payload)

    def update_record_by_id(
        self, table_id: str, record_id: str, update_fields: Dict[str, Any]
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
            endpoint = self.get_endpoint(table_id, record_id=record_id)
            # Prepare update payload
            payload = {
                "fieldKeyType": "dbFieldName",
                "record": {"fields": update_fields},
            }
            # PATCH method for partial update
            return self._make_request(Method.PATCH, endpoint=endpoint, json=payload)

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error updating record by ID: {e}")
            return None

    def find_record_by_field(
        self, table_id: str, field_name: str, field_value: Any
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
                {"fieldId": field_name, "operator": "is", "value": field_value},
            ]
            sort_value = [{"fieldId": field_name, "order": "asc"}]
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

            endpoint = self.get_endpoint(table_id)
            data = self._make_request(Method.GET, endpoint=endpoint, params=params)
            _logger.info("Find record by fields data %s", data)
            if data.get("records") and len(data["records"]) > 0:
                return data["records"][0]
            else:
                _logger.info(f"No record found with {field_name} = {field_value}")
                return None

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error finding record by field: {e}")
            return None

    def upsert_record(
        self,
        table_id: str,
        unique_field: str,
        unique_value: Any,
        update_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update if exists, insert if not exists (UPSERT)

        This is useful for Odoo migration where you want to sync data

        Args:
            table: The ID of the table
            unique_field: Field that should be unique (e.g., 'product_code')
            unique_value: Value of the unique field
            update_fields: Dictionary of field names and values

        Returns:
            Created or updated record
        """
        try:
            # Check if record exists
            existing_record = self.find_record_by_field(
                table_id, unique_field, unique_value
            )

            if existing_record:
                # Update existing record
                _logger.info(
                    f"Updating existing record with {unique_field} = {unique_value}"
                )
                return self.update_record_by_id(
                    table_id, existing_record["id"], update_fields
                )
            else:
                # Create new record
                _logger.info(
                    f"Creating new record with {unique_field} = {unique_value}"
                )
                return self.create_record(table_id, update_fields)

        except Exception as e:
            _logger.error(f"Error in upsert operation: {e}")
            return {}

    def delete_record(self, table_id: str, record_id: str) -> bool:
        """
        Delete a record
        Args:
            table: Table ID
            record_id: Record ID to delete
        Returns:
            True if successful, False otherwise
        """
        endpoint = self.get_endpoint(table_id, record_id=record_id)
        result = self._make_request(Method.DELETE, endpoint)
        return result is not None

    # ========== UTILITY METHODS ==========
    def list_tables(self, base: str) -> Optional[Dict]:
        """List all tables in the base"""
        url = f"/base/{base}/table"
        params = {"fieldKeyType": "name"}
        return self._make_request(Method.GET, url, params=params)

    def get_table_schema(self, table_id: str) -> Optional[Dict]:
        """Get table schema/fields"""
        return self._make_request(Method.GET, f"/table/{table_id}/field")

    def get_max_write_date_record(
        self, table_id: str, date_field: str = "write_date"
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
            endpoint = self.get_endpoint(table_id)
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
            # _logger.info("result : %s ", result)
            if result and result.get("records") and len(result["records"]) > 0:
                return result["records"][0]
            else:
                _logger.error(f"No records found in table {table_id}")
                return None

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error fetching max write_date record: {e}")
            return None

    def get_max_write_date_value(
        self, table_id: str, date_field: str = "write_date"
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
        record = self.get_max_write_date_record(table_id, date_field)
        if record and "fields" in record:
            return record["fields"].get(date_field)
        return None

    def get_records_after_date(
        self, table_id: str, date_field: str, after_date: str, limit: int = 100
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
            endpoint = self.get_endpoint(table_id)
            result = self._make_request(Method.GET, endpoint, params=params)
            return result.get("records", [])

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error fetching records after date: {e}")
            return []

    def download_complete_schema(self, base: str):
        """Download complete schema including tables and fields"""
        # Get all tables
        tables = self.list_tables(base)
        if not tables:
            return

        complete_schema = {
            "base_id": base,
            "download_date": datetime.now().isoformat(),
            "tables": [],
        }

        # Handle both list and dict responses
        if isinstance(tables, dict) and "records" in tables:
            table_list = tables["records"]
        elif isinstance(tables, list):
            table_list = tables
        else:
            _logger.info(f"Unexpected tables format: {type(tables)}")
            return complete_schema

        for table in table_list:
            table = table["id"]
            table_name = table.get("name", "Unknown")

            _logger.info(f"Processing table: {table_name}")

            # Get table details
            table_details = self.get_table_schema(table)

            # Get all fields
            field_list = []
            # fields = get_table_fields(table)

            table_schema = {
                "id": table,
                "name": table_name,
                "description": table.get("description", ""),
                "details": table_details,
            }

            complete_schema["tables"].append(table_schema)

        # Save to file
        filename = f"teable_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(complete_schema, f, indent=2, ensure_ascii=False)

        _logger.info(f"Schema saved to: {filename}")
        _logger.info(f"Total tables downloaded: {len(complete_schema['tables'])}")

        return complete_schema


client = TeableAPIClient(
    database="bse0fQ6EXNGdiMURvQs",
    api_token="teable_acc65mmZVTtEo9VcPja_M/ACnbw8UHoLtGX6HW52TYUgUArZegSjHQ3MTvNecwE=",
    base_url="https://teable-team-zervi-u34072.vm.elestio.app/api",
)

# field = {
#     "id": 110396,
#     "default_code": "LBR-10508",
#     "name": "Label RAZOR BACK",
#     "barcode": "LBR-10508",
#     "categ_id": "RM / Labels and  Badges",
#     "standard_price": 10.53030303030303,
#     "list_price": 1.0,
#     "qty_available": 112.0,
#     "uom_id": {"id": "recvxlSQn1zVotT1ifJ"},
#     "write_date": 1773903323.922646,
# }

# client.create_record(table="product", fields=field)


# client.update_record(
#     table="product", record_id="recoyZY1WUxSYnTnAcI", fields={"barcode": "AAA"}
# )

# client.upsert_record(
#     table="product",
#     unique_field="id",
#     unique_value="6",
#     update_fields={"barcode": "AAA5"},
# )

# write_date = client.get_max_write_date_record(table="product")
# print(write_date)

# uom_dict = {}
# uoms = client.get_records(table="uom").get("records")
# for uom in uoms:
#     # print(uom.get("id"))
#     # print(uom.get("fields").get("UOM"))
#     uom_dict[uom.get("fields").get("UOM")] = {"id": uom.get("id")}

# print(uom_dict)
