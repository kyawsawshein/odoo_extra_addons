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
from ..helper.teable_slae_order import TeableSaleOrderAPI

_logger = logging.getLogger(__name__)


class TeableAI(models.Model):
    _inherit = "teable.ai"

    def prepare_sale_order_line(
        self,
        line,
    ) -> SaleOrderLineData:
        return SaleOrderLineData(
            product_id=line.get("product_id"),
            product_uom_qty=line.get("uom_id"),
            product_uom_id=line.get("product_uom_id"),
            price_unit=line.get("price_unit"),
        )

    def prepare_order(
        self,
        customer_id: int,
    ) -> SaleOrderData:
        return SaleOrderData(
            partner_id=customer_id,
            date_order=fields.Datetime.now(),
        )

    def create_sale_order(self, values):
        self.env["sale.order"].create(values)

    def sync_table_sale_order(self):
        table = "sale_order"
        line_table = "sale_order_line"
        table_dict = self.get_table_id()
        table_id = table_dict.get(table)
        line_table_id = table_dict.get(line_table)

        api = self.env["api.config"].search([("name", "=", "Teable AI")])
        client = TeableSaleOrderAPI(database=api.database, api_token=api.token_key)

        if not table_id:
            raise ValidationError("Table Id not found!")

        if client:
            filter_list = [
                {"fieldId": "Status", "operator": "is", "value": "Confirmed"},
                {"fieldId": "Sync", "operator": "is", "value": "Pending"},
            ]
            sort_list = [{"fieldId": "Sale_Order", "order": "asc"}]
            table_sale_order = client.get_records(table_id, filter_list, sort_list)
            table_order_ids = [order.get("id") for order in table_sale_order]

            _logger.info("####### Sale order : %s ", table_sale_order)
            _logger.info("#### sale order ids ", table_order_ids)
            table_sale_order_data = client.get_sale_orders_with_lines_batch(
                table_id=table_id,
                line_table_id=line_table_id,
                order_ids=table_order_ids,
            )
            _logger.info("### sale order data %s", table_sale_order_data)
            values = []
            record_ids = []
            for table_order in table_sale_order_data:
                tb_order = table_order.get("order")
                tb_order_line = table_order.get("lines")
                _logger.info("### Order ### %s ", tb_order)
                _logger.info("### Order Line ### %s ", tb_order_line)
                order_line = []
                for line in tb_order_line:
                    field_data = line.get("fields")
                    product_dict = self.env["product.product"].search_read(
                        [
                            (
                                "default_code",
                                "=",
                                field_data.get("default_code").get("title"),
                            )
                        ],
                        fields=["id", "default_code", "uom_id"],
                    )[0]
                    line = SaleOrderLineData(
                        product_id=product_dict.get("id"),
                        product_uom_qty=field_data.get("Qty"),
                        product_uom_id=product_dict.get("uom_id")[0],
                        price_unit=field_data.get("Unit_Price"),
                    )
                    order_line.append(default_ids(line))
                _logger.info(
                    "##### Table order customer %s",
                    tb_order.get("fields").get("Customer").get("title"),
                )
                partner = self.env["res.partner"].search_read(
                    [
                        (
                            "name",
                            "=",
                            tb_order.get("fields").get("Customer").get("title"),
                        )
                    ],
                    fields=["name"],
                    limit=1,
                )[0]
                _logger.info("######### Partner %s ", partner)
                sale_order = self.prepare_order(customer_id=partner.get("id"))
                sale_order.order_line = order_line

                values.append(sale_order.__dict__)
                record_ids.append(tb_order.get("id"))
            _logger.info("#### values data list : %s ", values)
            _logger.info("#### record ids : %s ", record_ids)
            self.create_sale_order(values=values)
            for record in record_ids:
                client.update_record_by_id(
                    table_id=table_id,
                    record_id=record,
                    update_fields={"Sync": "Sync"},
                )
            _logger.info("# Picking Data In ")
