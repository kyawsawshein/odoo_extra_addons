import logging
from typing import Dict, List

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ...data_commom.datamodels.datamodel import (
    SaleOrderData,
    SaleOrderLineData,
    default_ids,
)
from ..helper.teable_endpoint import TeableAPIClient

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def add_line(
        self,
        line,
    ) -> SaleOrderLineData:
        return SaleOrderLineData(
            product_id=line.get("product_id"),
            product_uom_qty=line.get("uom_id"),
        )

    def _prepare_sale_order(self, lines, sale_order: SaleOrderData):
        lines = []
        for line in lines:
            _logger.info("### Line : %s", line)
            lines.append(default_ids(self.add_line(line)))

        sale_order.order_lines = lines

    def prepare_sale_order(
        self,
        customer_id: int,
    ) -> SaleOrderData:
        return SaleOrderData(
            customer_id=customer_id,
            date_order=fields.Datetime.now(),
        )

    def sync_table_sale_order(self):
        table = "sale_order_line"
        api = self.env["api.config"].search([("name", "=", "Teable AI")])
        client = TeableAPIClient(database=api.database, api_token=api.token_key)
        filter_list = [
            {"fieldId": "Status", "operator": "is", "value": "Done"},
        ]
        sort_list = [{"fieldId": "ID", "order": "asc"}]
        table_order_line = client.get_records(table, filter_list, sort_list)

        sale_order_data = self.prepare_sale_order(
            customer_id=1,
        )

        values = []
        for line in table_order_line:
            _logger.info("==================== sale order line %s", line.get("fields"))
            line_data = line.get("fields")
            product_dict = self.env["product.product"].search_read(
                [
                    (
                        "default_code",
                        "=",
                        line_data.get("Product").get("title"),
                    )
                ],
                fields=["id", "default_code", "uom_id"],
            )[0]
            _logger.info("### product dict %s ", product_dict)
            value = {
                "product_id": product_dict.get("id"),
                "uom_id": product_dict.get("uom_id")[0],
                "quantity": line_data.get("Qty"),
                # "price_unit": field_data.get("Cost"),
            }
            values.append(value)
        _logger.info("#### values data list : %s ", values)
        self._prepare_sale_order(lines=values, sale_order=sale_order_data)
        _logger.info("# Picking Data In : %s ", sale_order_data)
        sale_order = (
            self.env["stock.picking"]
            # .with_context(**context)
            .create(sale_order_data.__dict__)
        )
        sale_order.button_validate()
