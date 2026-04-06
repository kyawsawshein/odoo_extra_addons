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
        self.base_url = base_url

        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        _logger.info("Teable AI Connected...")

    def get_sql_payload(self, sql: str) -> Dict[str, Any]:
        return {"fieldKeyType": "dbFieldName", "sql": sql}

    def execute_sql_query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query on Teable"""
        try:
            # ✅ Fix 1: /base/ not /bases/
            url = f"{self.base_url}/base/{self.database}/sql-query"

            # ✅ Fix 2: "sql" not "query"
            # payload = {"sql": sql}
            payload = self.get_sql_payload(sql=sql)
            print(f"Executing SQL query: {sql}")
            print(f"URL: {url}")

            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            _logger.info(f"SQL query failed: {e}")
            print(f"SQL query failed: {e}")
            # Print response body for debugging
            if hasattr(e, "response") and e.response is not None:
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


def get_manufacture_orders_sql() -> str:
    return f"""
        SELECT "__id","Product", "Quantity", "Production_Raw_Material", "Finished_Goods"
        FROM "{BASE_ID}"."MO"
        WHERE "Status" = 'Done' AND "Name" = 'MO-3'
    """


def get_mo_raw_material_lines_sql() -> str:
    return f"""
        SELECT p."id" as product_id, p."default_code", raw."Consume_Qty", raw."Lot_ids", uom."uom_id", raw."Total_Cost"
        FROM "{BASE_ID}"."MO_Raw_Material" raw
            LEFT JOIN "{BASE_ID}"."Products" p ON (raw."Product"->>'id') = p."__id"
            LEFT JOIN "{BASE_ID}"."Units_of_Measure" uom ON (p."uom_id"->>'id') = uom."__id"
        WHERE raw."__id" IN ($raw_ids)
    """


def get_mo_finished_goods_lines_sql() -> str:
    return f"""
        SELECT p."id" as product_id,p."default_code",fgo."Finished_Qty",fgo."Cost", uom."uom_id", fgo."Lot_No"
        FROM "{BASE_ID}"."MO_Finished_Goods" fgo
            LEFT JOIN "{BASE_ID}"."Products" p ON (fgo."Product"->>'id') = p."__id"
            LEFT JOIN "{BASE_ID}"."Units_of_Measure" uom ON (p."uom_id"->>'id') = uom."__id"
        WHERE fgo."__id" IN ($goods_ids)
    """


def get_manufacture_orders() -> List:
    manufacture_orders = []
    mo_orders = client.execute_sql_query(sql=get_manufacture_orders_sql())
    print("Manufacture Orders:", mo_orders)
    for order in mo_orders.get("rows", []):
        raw_line_ids = [l["id"] for l in order.get("Production_Raw_Material", [])]
        goods_line_ids = [l["id"] for l in order.get("Finished_Goods", [])]
        if not raw_line_ids:
            manufacture_orders.append({"order": order, "raw_lines": []})
        raw_lines = client.execute_sql_query(
            sql=get_mo_raw_material_lines_sql().replace(
                "$raw_ids", ",".join([f"'{i}'" for i in raw_line_ids])
            )
        )
        if not goods_line_ids:
            manufacture_orders.append({"order": order, "goods_lines": []})
        goods_lines = client.execute_sql_query(
            sql=get_mo_finished_goods_lines_sql().replace(
                "$goods_ids", ",".join([f"'{i}'" for i in goods_line_ids])
            )
        )
        manufacture_orders.append(
            {"order": order, "raw_lines": raw_lines, "goods_lines": goods_lines}
        )
    return manufacture_orders


mo_orders = get_manufacture_orders()

print("Final Manufacture Orders with lines:", mo_orders)

# get_sale_orders = f"""
#     SELECT so."__id","Customer", p."partner_id", "Status","Order_Date","Delivery_Date","PO_No","Source_Location","Company","Sale_Team","Name","Sales_Order_Lines"
#     FROM "{BASE_ID}"."Sales_Orders" so
#         LEFT JOIN "{BASE_ID}"."Partners" p ON  (so."Customer"->>'id') = p."__id"
#     WHERE "Status" = 'Confirmed'
# """

# get_sale_order_lines = f"""
#     SELECT sol."__id",sol."default_code","Qty","Unit_Price","Job_No", p."id" as product_id, uom."uom_id"
#     FROM "{BASE_ID}"."Sales_Order_Lines" sol
#         LEFT JOIN "{BASE_ID}"."Products" p ON (sol."default_code"->>'id') = p."__id"
#         LEFT JOIN "{BASE_ID}"."Units_of_Measure" uom ON (p."uom_id"->>'id') = uom."__id"
#     WHERE sol."__id" IN ($line_ids)
# """


# orders = client.execute_sql_query(sql=get_sale_orders.format(BASE_ID1=BASE_ID, BASE_ID=BASE_ID))

# orders = client.execute_sql_query(
#     sql=get_sale_orders.replace("$BASE_ID", BASE_ID).replace("$BASE_ID", BASE_ID)
# )
# print("Orders with lines:", orders)
# sale_order = []

# for order in orders.get("rows", []):
#     line_ids = [l["id"] for l in order.get("Sales_Order_Lines", [])]
#     print("##### Line IDs for {}".format(line_ids))
#     if not line_ids:
#         sale_order.append({"order": order, "lines": []})
#     lines = client.execute_sql_query(
#         sql=get_sale_order_lines.replace("$BASE_ID", BASE_ID)
#         .replace("$BASE_ID", BASE_ID)
#         .replace("$line_ids", ",".join([f"'{i}'" for i in line_ids]))
#     )
#     sale_order.append({"order": order, "lines": lines})

# print("Final Sale Orders with lines:", sale_order)

# sql_str = f"""SELECT so."__id","Customer", p."partner_id", "Status","Order_Date","Delivery_Date","PO_No","Source_Location","Company","Sale_Team","Name","Sales_Order_Lines"
#         FROM "{BASE_ID}"."Sales_Orders" so
#         LEFT JOIN "{BASE_ID}"."Partners" p ON  (so."Customer"->>'id') = p."__id"
#         WHERE "Status" = \'Confirmed\' AND "Name" = \'SO-16\'
# """

# line_sql = f"""
# SELECT "__id","default_code","Qty","Unit_Price","Job_No","Products"."id" as product_id, "Products"."uom_id" as product_uom_id
# FROM "{BASE_ID}"."Sales_Order_Lines"
#     INNER JOIN "{BASE_ID}"."Products" p ON "Sales_Order_Lines"."default_code" = p."default_code"
# WHERE "__id" IN ($1)
# """

# line_sql = f"""
#     SELECT
#         sol."__id",
#         sol."default_code",
#         sol."Qty",
#         sol."Unit_Price",
#         sol."Job_No",
#         -- Extract text value from JSONB
#         (sol."default_code"->>'id') as product_id,
#         (sol."default_code"->>'title') as product_code,
#         -- Join with Products table using JSONB id
#         p."__id" as product_record_id,
#         p."uom_id"
#     FROM "{BASE_ID}"."Sales_Order_Lines" sol
#     LEFT JOIN "{BASE_ID}"."Products" p
#         ON (sol."default_code"->>'id') = p."__id"
#     WHERE sol."__id" IN ($1)
# """

# query = f"""
#     SELECT "__id","default_code","Qty","Unit_Price","Job_No"
#     FROM "{BASE_ID}"."Sales_Order_Lines"
#     WHERE "__id" IN ({ids_str})
#     """

# sql_str = f'SELECT * FROM "{BASE_ID}"."Sales_Orders" WHERE "Status" = \'Confirmed\''
# sale_order = client.execute_sql_query(sql=sql_str)


# # print("Sale Orders:", sale_order_line)
# for order in sale_order.get("rows", []):
#     print("########################")
#     print("Order :", order)
#     line_ids = [l["id"] for l in order.get("Sales_Order_Lines", [])]

#     print("Order ID for line query:", line_ids)
#     print(
#         client.execute_sql_query(
#             sql=f"""
#             SELECT *
#             FROM "{BASE_ID}"."Sales_Order_Lines"
#             WHERE "__id" IN ({",".join([f"'{i}'" for i in line_ids])})
#             """
#         )
#     )
