import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from odoo import fields, models
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

from ..helper.teable_endpoint import TeableAPIClient

_logger = logging.getLogger(__name__)


class Product:
    id: int
    default_code: str
    name: str
    barcode: str
    categ_id: int
    standard_price: float
    list_price: float
    qty_available: float
    uom_id: int
    write_date: int


class ProductProduct(models.Model):
    _inherit = "product.product"

    def get_table_id(self) -> Dict:
        table_dict = {}
        for table in self.env["teable.ai"].search_read([], fields=["name", "table"]):
            table_dict[table.get("name")] = table.get("table")

        return table_dict

    def teable_uom(self, table_dict: Dict) -> Dict:
        api = self.env["api.config"].search([("name", "=", "Teable AI")])
        client = TeableAPIClient(database=api.database, api_token=api.token_key)
        uom_teable = client.get_records(table_id=table_dict.get("uom"))
        uom_dict = {}
        for uom in uom_teable:
            uom_dict[uom.get("fields").get("UOM")] = {"id": uom.get("id")}
        return uom_dict

    def teable_stock_lot(self, limit: int = 10, order: str = "write_date asc") -> Dict:
        table = "stock_lot"
        api = self.env["api.config"].search([("name", "=", "Teable AI")])
        client = TeableAPIClient(database=api.database, api_token=api.token_key)
        uom_dict = self.teable_uom()
        last_write_date = client.get_max_write_date_record(table)

        _logger.info("last write date %s", last_write_date)
        timestamp = last_write_date.get("fields").get("write_date")
        write_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        write_date = write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        _logger.info(
            "=========== The last product write data : %s, %s",
            write_date,
            type(write_date),
        )

        domain = [("write_date", ">", write_date)]
        if filter:
            domain.extend(filter)

        products = self.env["stock.lot"].search_read(
            domain,
            fields=[
                "id",
                "name",
                "product_id",
                "product_qty",
                "write_date",
            ],
            limit=limit,
            order=order,
        )
        _logger.info("Product total product count : %s .", len(products))
        for product in products:
            for key, value in product.items():
                if isinstance(value, tuple):
                    product[key] = value[1]
                if isinstance(value, bool):
                    product[key] = None
                if key == "uom_id":
                    product[key] = {"id": "recvxlSQn1zVotT1ifJ"}
                if key == "write_date":
                    product[key] = value.timestamp()
            try:
                client.upsert_record(
                    table="product",
                    unique_field="id",
                    unique_value=product.get("id"),
                    update_fields=proudct,
                )

            except Exception as err:
                _logger.error("Error ", str(err))

    def _update_record_table(
        self,
        uom_dict: Dict,
        records: List,
        table: str,
        unique_field: str,
        unique_value: Any,
    ):
        for rec in records:
            for key, value in rec.items():
                if isinstance(value, tuple):
                    rec[key] = value[1]
                if isinstance(value, bool):
                    rec[key] = None
                if key == "uom_id":
                    rec[key] = uom_dict.get(value[1])
                if key == "write_date":
                    rec[key] = value.timestamp()
            _logger.info("Product %s", rec)
            try:
                client.upsert_record(
                    table=table,
                    unique_field=records,
                    unique_value=unique_value,
                    update_fields=rec,
                )

            except Exception as err:
                _logger.error("Error ", str(err))

    def sync_teable_ai(
        self,
        filter_domain: List = None,
        limit: int = 1000,
        order: str = "write_date asc",
    ):
        start_time = datetime.now()
        table_dict = self.get_table_id()
        _logger.info("#### Teable ID : %s ", table_dict)
        table_id = table_dict.get("product")

        api = self.env["api.config"].search([("name", "=", "Teable AI")])
        client = TeableAPIClient(database=api.database, api_token=api.token_key)
        uom_dict = self.teable_uom(table_dict)
        _logger.info("UOM dict : %s", uom_dict)

        domain = [("type", "=", "consu")]

        last_write_date = client.get_max_write_date_record(table_id)
        if last_write_date:
            timestamp = last_write_date.get("fields").get("write_date")
            write_date = datetime.fromtimestamp(timestamp).strftime(
                DEFAULT_SERVER_DATETIME_FORMAT
            )
            _logger.info("Write date %s ", write_date)
            domain.append(("write_date", ">", write_date))

        if filter_domain:
            domain.extend(filter_domain)

        products = self.search_read(
            domain,
            fields=[
                "id",
                "default_code",
                "name",
                "barcode",
                "categ_id",
                "standard_price",
                "list_price",
                "qty_available",
                "uom_id",
                "write_date",
            ],
            limit=limit,
            order=order,
        )
        _logger.info("Product total product count : %s .", len(products))

        for product in products:
            for key, value in product.items():
                if isinstance(value, tuple):
                    product[key] = value[1]
                if isinstance(value, bool):
                    product[key] = None
                if key == "uom_id":
                    product[key] = uom_dict.get(value[1])
                if key == "write_date":
                    product[key] = value.timestamp()
            _logger.info("Product %s", product)
            try:
                client.upsert_record(
                    table="product",
                    unique_field="id",
                    unique_value=product.get("id"),
                    update_fields=product,
                )
            except Exception as err:
                _logger.error("Error ", str(err))

        # stocks = self.teable_stock_quant(client)
        # _logger.info("### stock quant data count: %s ", stocks)
        # self._update_record_table(
        #     client=client,
        #     uom_dict=uom_dict,
        #     records=stocks,
        #     table="stock",
        #     unique_field="product_id",
        #     unique_value="",
        # )

        end_time = datetime.now()
        _logger.info(
            "Done Cron toaken time : %s for record count %s ",
            end_time - start_time,
            len(products),
        )

    def teable_stock_quant(
        self,
        client: TeableAPIClient,
        filter_domain: List = None,
        limit: int = 100,
        order: str = "write_date asc",
    ):
        start_time = datetime.now()
        table = "stock"
        domain = []

        last_write_date = client.get_max_write_date_record(table)
        _logger.info("The last write date data  %s ", last_write_date)
        if last_write_date:
            timestamp = last_write_date.get("fields").get("write_date")
            write_date = datetime.fromtimestamp(timestamp).strftime(
                DEFAULT_SERVER_DATETIME_FORMAT
            )
            _logger.info("Write date %s ", write_date)
            domain.append(("write_date", ">", write_date))

        if filter_domain:
            domain.extend(filter_domain)

        stocks = self.env["stock.quant"].search_read(
            domain,
            fields=[
                "product_id",
                "location_id",
                "product_categ_id",
                "lot_id",
                "reserved_quantity",
                "available_quantity",
                "value",
                "product_uom_id",
                "write_date",
            ],
            limit=limit,
            order=order,
        )
        _logger.info("Product total stock count : %s .", len(stocks))

        return stocks
