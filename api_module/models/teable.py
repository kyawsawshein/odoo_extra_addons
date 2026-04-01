import datetime
import json
import logging
from datetime import datetime
from typing import Any, Dict, List

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
from ..datamodels.datamodel import TeablePartner, TeableProduct
from ..helper.teable_endpoint import TeableAPIClient

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

    def _prepare_record(
        self,
        records: List,
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
        records: List,
        table_id: str,
        unique_field: str,
    ):
        for rec in records:
            try:
                TEABLE.upsert_record(
                    table_id=table_id,
                    unique_field=unique_field,
                    unique_value=rec.get(unique_field),
                    update_fields=rec,
                )

            except Exception as err:
                _logger.error("Error ", str(err))

    def _prepare_product_table(
        self,
        uom_dict: Dict,
        records: List,
    ):
        for rec in records:
            for key, value in rec.items():
                if isinstance(value, (tuple, list)):
                    rec[key] = value[1]
                if isinstance(value, bool):
                    rec[key] = value or None
                if key == "uom_id":
                    rec[key] = uom_dict.get(value[1])
                if key == "write_date":
                    rec[key] = value.timestamp()
            _logger.info("Product %s", rec)

    def produce_product_table(self, table_id: str, products: List):
        table_dict = self.get_table_id()
        uom_dict = self.teable_uom(table_dict)
        self._prepare_product_table(
            uom_dict=uom_dict,
            records=products,
        )
        self._update_table(
            records=products, table_id=table_id, unique_field="default_code"
        )

    def product_partner_table(self, table_id: str, partners: List[Dict]):
        self._prepare_record(records=partners)
        self._update_table(
            records=partners,
            table_id=table_id,
            unique_field="id",
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
                ).produce(table_id=table_id, records=records, method=method)

    def produce(self, table_id: str, records: List[Dict], method: str):
        with Registry(self.env.cr.dbname).cursor() as new_cr:
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            teable = new_env["teable.ai"]
            getattr(teable, method)(table_id, records)
            _logger.info("###### Done job")

    def sync_teable_product(
        self,
        filter_domain: List = None,
        limit: int = 1000,
        order: str = "write_date asc",
    ):
        start_time = datetime.now()
        table_dict = self.get_table_id()
        _logger.info("#### Teable ID : %s ", table_dict)
        table_id = table_dict.get("product")
        if not table_id:
            raise ValidationError("Table Id not found!")

        if self.check_client:
            domain = [("default_code", "!=", False)]
            last_write_date = TEABLE.get_max_write_date_record(table_id)
            if last_write_date:
                timestamp = last_write_date.get("fields").get("write_date")
                if timestamp:
                    write_date = datetime.fromtimestamp(timestamp).strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT
                    )
                    _logger.info("Write date %s ", write_date)
                    domain.append(("write_date", ">", write_date))

            if filter_domain:
                domain.extend(filter_domain)

            fields = TeableProduct.get_fields(TeableProduct)
            _logger.info("#### Domain : %s  and Fiedls List : %s", domain, fields)
            products = self.env["product.product"].search_read(
                domain,
                fields=fields,
                limit=limit,
                order=order,
            )
            _logger.info("Product total product count : %s .", len(products))
            self.with_delay_table_produce(
                table_id=table_id, record_list=products, method="produce_product_table"
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
        limit: int = 10,
        order: str = "write_date asc",
    ):
        start_time = datetime.now()
        table_dict = self.get_table_id()
        _logger.info("#### Teable ID : %s ", table_dict)
        table_id = table_dict.get("partner")
        if not table_id:
            raise ValidationError("Table Id not found!")

        if self.check_client:
            domain = []
            last_write_date = TEABLE.get_max_write_date_record(table_id)
            _logger.info("##### last write date record %s ", last_write_date)
            if last_write_date:
                timestamp = last_write_date.get("fields").get("write_date")
                if timestamp:
                    write_date = datetime.fromtimestamp(timestamp).strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT
                    )
                    _logger.info("Write date %s ", write_date)
                    domain.append(("write_date", ">", write_date))

            if filter_domain:
                domain.extend(filter_domain)

            fields = TeablePartner.get_fields(TeablePartner)
            _logger.info("#### Domain : %s  and Fiedls List : %s", domain, fields)
            partners = self.env["res.partner"].search_read(
                domain,
                fields=fields,
                limit=limit,
                order=order,
            )
            _logger.info("Partners total count : %s .", len(partners))

            self.with_delay_table_produce(
                table_id=table_id, record_list=partners, method="product_partner_table"
            )

            end_time = datetime.now()
            _logger.info(
                "Done Cron toaken time : %s for record count %s ",
                end_time - start_time,
                len(partners),
            )
