import logging
from itertools import groupby
from typing import Dict, List

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ...data_commom.datamodels.datamodel import (
    SaleOrderData,
    SaleOrderLineData,
    default_ids,
)
from ..helper.teable_endpoint import TeableAPIClient

_logger = logging.getLogger(__name__)


class TeableAI(models.Model):
    _inherit = "teable.ai"

    def add_line(
        self,
        line,
    ) -> SaleOrderLineData:
        return SaleOrderLineData(
            product_id=line.get("product_id"),
            product_uom_qty=line.get("uom_id"),
            product_uom_id=line.get("product_uom_id"),
            price_unit=line.get("price_unit"),
        )

    def _prepare_sale_order(self, lines):

        sale_order = SaleOrderData(
            customer_id=customer_id,
            date_order=fields.Datetime.now(),
        )
        lines = []
        for line in lines:
            lines.append(default_ids(self.add_line(line)))

        sale_order.order_lines = lines

    def create_sale_order(
        self,
        customer_id: int,
    ) -> SaleOrderData:
        return SaleOrderData(
            customer_id=customer_id,
            date_order=fields.Datetime.now(),
        )

    def sync_table_sale_order(self):
        table = "sale_order"
        table_dict = self.get_table_id()
        table_id = table_dict.get(table)

        api = self.env["api.config"].search([("name", "=", "Teable AI")])
        client = TeableAPIClient(database=api.database, api_token=api.token_key)

        if not table_id:
            raise ValidationError("Table Id not found!")

        if client:
            filter_list = [
                {"fieldId": "Status", "operator": "is", "value": "Confirmed"},
            ]
            sort_list = [{"fieldId": "Sale_Order", "order": "asc"}]
            sale_order_line = client.get_records(table_id, filter_list, sort_list)

            _logger.info("####### Sale order lines : %s ", sale_order_line)
            values = []
            record_ids = []
            # for line in sale_order_line:
            #     field_data = line.get("fields")
            #     product_dict = self.env["product.product"].search_read(
            #         [
            #             (
            #                 "default_code",
            #                 "=",
            #                 field_data.get("default_code").get("title"),
            #             )
            #         ],
            #         fields=["id", "default_code", "uom_id"],
            #     )[0]

            #     _logger.info("### product dict %s ", product_dict)

            #     value = {
            #         "partner_id": "",
            #         "product_id": product_dict.get("id"),
            #         "product_uom_id": product_dict.get("uom_id")[0],
            #         "product_uom_qty": field_data.get("Qty"),
            #         "price_unit": field_data.get("Unit_Price"),
            #     }
            #     values.append(value)
            #     record_ids.append(line.get("id"))
            # _logger.info("#### values data list : %s ", values)

            # for lines in groupby(values, key=lambda v: v[])

            # self.create_sale_order(values=values)
            # for record in record_ids:
            #     client.update_record_by_id(
            #         table_id=table_id,
            #         record_id=record,
            #         update_fields={"received": "Received"},
            #     )

            # _logger.info("# Picking Data In ")
