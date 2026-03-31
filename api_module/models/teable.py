import datetime
import json
import logging
from datetime import datetime
from typing import Dict

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

from ..helper.teable_endpoint import TeableAPIClient

_logger = logging.getLogger(__name__)

TEABLE = None


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

    # def get_client(self):
    #     api = self.env["api.config"].search([("name", "=", "Teable AI")])
    #     client = TeableAPIClient(database=api.database, api_token=api.token_key)
    #     return client

    def teable_uom(self, table_dict: Dict) -> Dict:
        uom_teable = TEABLE.get_records(table_id=table_dict.get("uom"))
        uom_dict = {}
        for uom in uom_teable:
            uom_dict[uom.get("fields").get("UOM")] = {"id": uom.get("id")}
        return uom_dict

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
                TEABLE.upsert_record(
                    table_id=table,
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
        table_id = table_dict.get("res_partner")

        if TEABLE:
            uom_dict = self.teable_uom(table_dict)
            _logger.info("UOM dict : %s", uom_dict)

            domain = []
            last_write_date = TEABLE.get_max_write_date_record(table_id)
            if last_write_date:
                timestamp = last_write_date.get("fields").get("write_date")
                write_date = datetime.fromtimestamp(timestamp).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT
                )
                _logger.info("Write date %s ", write_date)
                domain.append(("write_date", ">", write_date))

            if filter_domain:
                domain.extend(filter_domain)

            partners = self.search_read(
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
            _logger.info("Product total product count : %s .", len(partners))

            for partner in partners:
                for key, value in partner.items():
                    if isinstance(value, tuple):
                        partner[key] = value[1]
                    if isinstance(value, bool):
                        partner[key] = None
                    if key == "uom_id":
                        partner[key] = uom_dict.get(value[1])
                    if key == "write_date":
                        partner[key] = value.timestamp()
                _logger.info("Product %s", partner)
                try:
                    client.upsert_record(
                        table="product",
                        unique_field="id",
                        unique_value=partner.get("id"),
                        update_fields=partner,
                    )
                except Exception as err:
                    _logger.error("Error ", str(err))

            end_time = datetime.now()
            _logger.info(
                "Done Cron toaken time : %s for record count %s ",
                end_time - start_time,
                len(products),
            )
