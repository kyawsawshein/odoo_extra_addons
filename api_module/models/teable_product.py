import datetime
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.modules.registry import Registry
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

from ...data_commom.datamodels.datamodel import (
    LineData,
    MoveData,
    PickingData,
    default_ids,
)
from ..datamodels.datamodel import (
    TeableID,
    TeablePartner,
    TeableProduct,
    TeableStockLot,
)
from ..helper.teable_endpoint import TeableAPIClient
from ..query.query import PartnerSQL, ProductSQL, StockSQL
from .teable import get_teable_client

_logger = logging.getLogger(__name__)

LIMIT = 20


class Teable(models.Model):
    _inherit = "teable.ai"

    # def get_max_write_date(self, table_id: int) -> Optional[str]:
    #     write_date = "1970-01-19"
    #     last_write_date = get_teable_client(self).get_max_write_record(table_id)
    #     _logger.info("##### last write date record %s ", last_write_date)
    #     if last_write_date:
    #         timestamp = last_write_date.get("fields").get("write_date")
    #         if timestamp:
    #             write_date = datetime.fromtimestamp(timestamp)
    #             return write_date
    #     return write_date

    def _prepare_record(
        self,
        records: List[Dict],
    ):
        for rec in records:
            for key, value in rec.items():
                if isinstance(value, (tuple, list)):
                    rec[key] = value[1]
                if isinstance(value, bool):
                    rec[key] = value or None
                if key == "write_date":
                    rec[key] = value.timestamp()

        return records

    def _prepare_product_table(self, records: List[Dict]):
        table_dict = self.get_table_id()
        uom_dict = self.teable_uom(table_dict)
        for rec in records:
            for key, value in rec.items():
                if key == "uom_id":
                    rec[key] = uom_dict.get(value)
            _logger.info("Product %s", rec)

    def prepare_stock_lot_table(self, stock_lots: List[Dict]):
        table = "product"
        table_dict = self.get_table_id()
        product_table_id = table_dict.get(table).teable_id
        if not product_table_id:
            raise ValidationError("Product table id not found!")

        codes = [lot.get("product") for lot in stock_lots]
        products = self._get_teable_client().get_products(codes=codes)
        _logger.info("Products %s", products)
        for lot in stock_lots:
            product = products.get(lot.get("product"))
            if product:
                lot["product"] = product.get("id")

    # def _update_product_table(
    #     self,
    #     records: List[Dict],
    #     table_id: TeableID,
    #     unique_field: str,
    # ):
    #     unique_values = ",".join([f"'{rec.get(unique_field)}'" for rec in records])
    #     get_teable_client(self).upsert_product_record(
    #         table_id=table_id.teable_id,
    #         table_name=table_id.name,
    #         unique_field=unique_field,
    #         unique_value=unique_values,
    #         update_records=records,
    #     )

    def produce_stock_lot_table(
        self, table: Dict, stock_lots: List[Dict], unique_field: str
    ):
        table = TeableID(**table)
        self.prepare_stock_lot_table(stock_lots=stock_lots)
        self.update_table(
            records=stock_lots,
            table=table,
            unique_field=unique_field,
        )

    def product_produce_table(
        self, table: Dict, stock_lots: List[Dict], unique_field: str
    ):
        teable = TeableID(**table)
        self._update_table(
            records=stock_lots,
            table=teable,
            unique_field=unique_field,
        )

    def sync_product_teable(
        self,
        teable_name: str = "Products",
        filter_domain: List = None,
        limit: int = 1000,
        order: str = "write_date asc",
    ):
        start_time = datetime.now()
        table_dict = self.get_table_id()
        table = table_dict.get(teable_name)
        if not table:
            raise ValidationError("Table Id not found!")

        if self.check_client:
            write_date = self.get_max_write_date(table.teable_id)
            _logger.info("Write date %s ", write_date)

            self.env.cr.execute(ProductSQL.producdt, (write_date,))
            products = self.env.cr.dictfetchall()
            _logger.info("Product total product count : %s .", len(products))
            self._prepare_product_table(records=products)
            _logger.info("###### product %s ", products)
            self.with_delay_table_produce(
                table_id=table.__dict__,
                record_list=products,
                method="product_produce_table",
                unique_field="default_code",
            )
            end_time = datetime.now()
            _logger.info(
                "Done Cron toaken time : %s for record count %s ",
                end_time - start_time,
                len(products),
            )

    def sync_table_lot(
        self,
        teable_name: str = "stock_lot",
        filter_domain: List = None,
        limit: int = 10,
        order: str = "write_date asc",
    ):
        table_dict = self.get_table_id()
        table = table_dict.get(teable_name)
        if not table:
            raise ValidationError("Table Id not found!")

        if self.check_client:
            write_date = self.get_max_write_date(table.teable_id)
            _logger.info("Write date %s ", write_date)

            self.env.cr.execute(StockSQL.stock_lot, (write_date,))
            stock_lots = self.env.cr.dictfetchall()
            _logger.info("Stock lot total count : %s .", len(stock_lots))
            self.with_delay_table_produce(
                table=table.__dict__,
                record_list=stock_lots,
                method="produce_stock_lot_table",
                unique_field="id",
            )

            end_time = datetime.now()
            _logger.info(
                "Done Cron toaken time : %s for record count %s ",
                end_time - start_time,
                len(stock_lots),
            )
