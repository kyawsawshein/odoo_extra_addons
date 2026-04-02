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
from ..datamodels.datamodel import TeablePartner, TeableProduct, TeableStockLot
from ..helper.teable_endpoint import TeableAPIClient
from ..query.query import PartnerSQL, ProductSQL, StockSQL

_logger = logging.getLogger(__name__)

TEABLE = None

LIMIT = 100


class Teable(models.Model):
    _name = "teable.ai"
    _description = "Teable AI"

    name = fields.Char(string="Table Name", required=True)
    table = fields.Char(string="Table ID", required=True)

    def _register_hook(self):
        """Called once per Odoo worker at startup."""
        super()._register_hook()
        global TEABLE
        if not TEABLE:
            try:
                api = self.env["api.config"].search([("name", "=", "Teable AI")])
                TEABLE = TeableAPIClient(database=api.database, api_token=api.token_key)
                _logger.info("Created Teable.ai connection.")
            except Exception as err:
                _logger.error("Failed to connect to Teable.ai: %s", str(err))

    def check_client(self) -> bool:
        if not TEABLE:
            _logger.error("Cannot update Meili index: No Meilisearch connection")
            self._register_hook()
            return False
        return True

    def get_table_id(self) -> Dict:
        table_dict = {}
        for table in self.search_read([], fields=["name", "table"]):
            table_dict[table.get("name")] = table.get("table")

        return table_dict

    def teable_uom(self, table_dict: Dict) -> Dict:
        uom_teable = TEABLE.get_records(table_id=table_dict.get("uom"))
        uom_dict = {}
        for uom in uom_teable:
            uom_dict[uom.get("fields").get("UOM")] = {"id": uom.get("id")}
        return uom_dict

    def get_max_write_date(self, table_id: str) -> Optional[str]:
        write_date = "1970-03-19"
        last_write_date = TEABLE.get_max_write_date_record(table_id)
        _logger.info("##### last write date record %s ", last_write_date)
        if last_write_date:
            timestamp = last_write_date.get("fields").get("write_date")
            if timestamp:
                write_date = datetime.fromtimestamp(timestamp).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT
                )
                return write_date
        return write_date

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

    def _update_table(
        self,
        records: List[Dict],
        table_id: str,
        unique_field: str,
    ):
        for rec in records:
            TEABLE.upsert_record(
                table_id=table_id,
                unique_field=unique_field,
                unique_value=rec.get(unique_field),
                update_fields=rec,
            )

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
        product_table_id = table_dict.get(table)
        if not product_table_id:
            raise ValidationError("Product table id not found!")

        for lot in stock_lots:
            for key, value in lot.items():
                if key == "product":
                    product = TEABLE.find_product_by_code(
                        table_id=product_table_id,
                        field_name="default_code",
                        field_value=value,
                    )
                    _logger.info("##### product table data %s", product)
                    lot[key] = product

    def produce_table(self, table_id: str, stock_lots: List[Dict], unique_field: str):
        self._update_table(
            records=stock_lots,
            table_id=table_id,
            unique_field=unique_field,
        )

    @staticmethod
    def split_by_batch(lst, batch_size):
        for i in range(0, len(lst), batch_size):
            yield lst[i : i + batch_size]

    def with_delay_table_produce(
        self,
        table_id: str,
        record_list: List[Dict],
        method: str,
        unique_field: str,
        channel: str = "root",
    ):

        if record_list:
            limit = (
                int(self.env["ir.config_parameter"].sudo().get_param("sync.batch"))
                or LIMIT
            )
            for records in self.split_by_batch(record_list, limit):
                self.with_delay(
                    channel=channel,
                    description=f"Teable AI Sync Table : {table_id}, methbod {method} : {len(records)}",
                ).produce(
                    table_id=table_id,
                    records=records,
                    method=method,
                    unique_field=unique_field,
                )

    def produce(
        self, table_id: str, records: List[Dict], method: str, unique_field: str
    ):
        with Registry(self.env.cr.dbname).cursor() as new_cr:
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            teable = new_env["teable.ai"]
            getattr(teable, method)(table_id, records, unique_field)
            _logger.info("###### Done job")

    def sync_teable_product(
        self,
        filter_domain: List = None,
        limit: int = 1000,
        order: str = "write_date asc",
    ):
        start_time = datetime.now()
        table_dict = self.get_table_id()
        table_id = table_dict.get("product")
        if not table_id:
            raise ValidationError("Table Id not found!")

        if self.check_client:
            domain = [("default_code", "!=", False)]
            write_date = self.get_max_write_date(table_id)
            _logger.info("Write date %s ", write_date)
            domain.append(("write_date", ">", write_date))

            self.env.cr.execute(ProductSQL.producdt, (write_date,))
            products = self.env.cr.dictfetchall()
            _logger.info("Product total product count : %s .", len(products))
            self._prepare_product_table(records=products)
            _logger.info("###### product %s ", products)
            self.with_delay_table_produce(
                table_id=table_id,
                record_list=products,
                method="produce_table",
                unique_field="default_code",
            )
            end_time = datetime.now()
            _logger.info(
                "Done Cron toaken time : %s for record count %s ",
                end_time - start_time,
                len(products),
            )

    def sync_table_partner(
        self,
        filter_domain: List = None,
        limit: int = 100,
        order: str = "write_date asc",
    ):
        start_time = datetime.now()
        table_dict = self.get_table_id()
        table_id = table_dict.get("partner")
        if not table_id:
            raise ValidationError("Table Id not found!")

        if self.check_client:
            write_date = self.get_max_write_date(table_id)
            _logger.info("Write date %s ", write_date)

            self.env.cr.execute(PartnerSQL.partner, (write_date,))
            partners = self.env.cr.dictfetchall()
            _logger.info("Partners total count : %s .", len(partners))
            # self._prepare_record(records=partners)
            self.with_delay_table_produce(
                table_id=table_id,
                record_list=partners,
                method="produce_table",
                unique_field="id",
            )

            end_time = datetime.now()
            _logger.info(
                "Done Cron toaken time : %s for record count %s ",
                end_time - start_time,
                len(partners),
            )

    def sync_table_lot(
        self,
        filter_domain: List = None,
        limit: int = 10,
        order: str = "write_date asc",
    ):
        start_time = datetime.now()
        table_dict = self.get_table_id()
        table_id = table_dict.get("stock_lot")
        if not table_id:
            raise ValidationError("Table Id not found!")

        if self.check_client:
            write_date = self.get_max_write_date(table_id)
            _logger.info("Write date %s ", write_date)

            self.env.cr.execute(StockSQL.stock_lot, (write_date,))
            stock_lots = self.env.cr.dictfetchall()
            _logger.info("Stock lot total count : %s .", len(stock_lots))
            self.prepare_stock_lot_table(stock_lots=stock_lots)
            self.with_delay_table_produce(
                table_id=table_id,
                record_list=stock_lots,
                method="produce_table",
                unique_field="name",
            )

            end_time = datetime.now()
            _logger.info(
                "Done Cron toaken time : %s for record count %s ",
                end_time - start_time,
                len(stock_lots),
            )
