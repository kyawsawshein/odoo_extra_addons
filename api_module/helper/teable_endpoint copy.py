import json
import logging
from typing import Any, Dict, List

import requests

_logger = logging.getLogger(__name__)


class TeableAPIClient:
    """Teable API client"""

    def __init__(self, database: str, api_token: str, base_url: str = None):
        self.database = database
        self.api_token = api_token
        self.base_url = base_url or "https://app.teable.ai/api"

        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        _logger.info("Teable AI Connected...")

    def execute_sql_query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query on Teable"""
        try:
            # ✅ Fix 1: /base/ not /bases/
            url = f"{self.base_url}/base/{self.database}/sql-query"

            # ✅ Fix 2: "sql" not "query"
            payload = {"sql": sql}

            print(f"Executing SQL query: {sql}")
            print(f"URL: {url}")

            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            _logger.info(f"SQL query failed: {e}")
            print(f"SQL query failed: {e}")
            # Print response body for debugging
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response body: {e.response.text}")
            return []


TEABLE_API_URL = "https://app.teable.ai/api"
BASE_ID = "bsez0Y8svP1AV6SJyPa"
TEABLE_APP_TOKEN = "teable_acc8IjiWjSVYXOWHVns_6AnnmMilIL8PpVWrxUtso4heAtwZBrFma6TAZClEYHY="

client = TeableAPIClient(
    database=BASE_ID,
    api_token=TEABLE_APP_TOKEN,
    base_url=TEABLE_API_URL,
)

# ✅ Fix 3: No "$" prefix, and use dbTableName (not display name)
# First, find your actual dbTableName by calling:
#   GET https://app.teable.ai/api/base/bsez0Y8svP1AV6SJyPa/table
# Then use it in the query:
# tblOClNHnF6vS07tBXS
# product = client.execute_sql_query(
#     f'SELECT CAST(COUNT(*) AS text) as "count" FROM "${BASE_ID}"."tblOClNHnF6vS07tBXS"'
# )
product = client.execute_sql_query(
    'SELECT CAST(COUNT(*) AS text) as "count" FROM "bsez0Y8svP1AV6SJyPa"."Product"'
)

print("Product count:", product)