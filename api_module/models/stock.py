import logging
from typing import Dict, List

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ...data_commom.datamodels.datamodel import (
    LineData,
    MoveData,
    PickingData,
    default_ids,
)
from ..helper.teable_endpoint import TeableAPIClient
from .teable import TEABLE

_logger = logging.getLogger(__name__)


class Teable(models.Model):
    _inherit = "teable.ai"

    def add_move_line(
        self,
        line,
        picking: PickingData,
    ) -> LineData:
        return LineData(
            product_id=line.get("product_id"),
            product_uom_id=line.get("uom_id"),
            location_id=picking.location_id,
            location_dest_id=picking.location_dest_id,
            quantity=line.get("quantity"),
            lot_name=line.get("lot_name"),
        )

    def add_move(self, line, picking: PickingData) -> MoveData:
        return MoveData(
            location_id=picking.location_id,
            location_dest_id=picking.location_dest_id,
            product_id=line.get("product_id"),
            product_uom=line.get("uom_id"),
            product_uom_qty=line.get("quantity"),
            price_unit=line.get("price_unit"),
        )

    def _prepare_move_in(self, lines: List[Dict], picking: PickingData) -> List:
        moves = []
        for line in lines:
            _logger.info("### Line : %s", line)
            move = self.add_move(line, picking)
            move.picking_type_id = picking.picking_type_id
            move.move_line_ids = [
                default_ids(
                    self.add_move_line(line, picking),
                )
            ]
            moves.append(default_ids(move))
        return moves

    def prepare_picking(
        self,
        picking_type_id: int,
        location_id: int,
        location_dest_id: int,
    ) -> PickingData:
        picking = PickingData(
            picking_type_id=picking_type_id,
            location_id=location_id,
            location_dest_id=location_dest_id,
            date_done=fields.Datetime.now(),
        )
        return picking

    def create_picking_lines_in(self, context: Dict, values: List[Dict]):
        location_id = 12
        location_dest_id = 5
        picking_data = self.prepare_picking(
            picking_type_id=1,
            location_id=location_id,
            location_dest_id=location_dest_id,
        )
        moves = self._prepare_move_in(
            lines=values,
            picking=picking_data,
        )
        picking_data.move_ids = moves
        _logger.info("# Picking Data In : %s ", picking_data)
        return (
            self.env["stock.picking"]
            .with_context(**context)
            .create(picking_data.__dict__)
        )

    def do_picking(self, values: List[Dict]):
        context = {"default_picking_type_id": 1}
        picking = self.create_picking_lines_in(context, values)

        # se face receptia
        if picking.move_ids:
            picking.action_assign()
            if picking.state == "assigned":
                picking.button_validate()

        _logger.info("Done validaet picking for in.")

    def sync_table_finished_goods(self):
        table = "mo_finished_goods"
        table_dict = self.get_table_id()
        table_id = table_dict.get(table)

        api = self.env["api.config"].search([("name", "=", "Teable AI")])
        TEABLE = TeableAPIClient(database=api.database, api_token=api.token_key)

        if not table_id:
            raise ValidationError("Table Id not found!")

        if TEABLE:
            filter_list = [
                {"fieldId": "Status", "operator": "is", "value": "Done"},
                {"fieldId": "Status", "operator": "is", "value": "Done"},
            ]
            sort_list = [{"fieldId": "ID", "order": "asc"}]
            finished_goods = TEABLE.get_records(table_id, filter_list, sort_list)

            values = []
            record_ids = []
            for goods in finished_goods:
                field_data = goods.get("fields")
                product_dict = self.env["product.product"].search_read(
                    [
                        (
                            "default_code",
                            "=",
                            field_data.get("Product").get("title"),
                        )
                    ],
                    fields=["id", "default_code", "uom_id"],
                )[0]

                _logger.info("### product dict %s ", product_dict)

                value = {
                    "product_id": product_dict.get("id"),
                    "uom_id": product_dict.get("uom_id")[0],
                    "quantity": field_data.get("Finished_Qty"),
                    "lot_name": field_data.get("Lot_No"),
                    "price_unit": field_data.get("Cost"),
                }
                values.append(value)
                record_ids.append(goods.get("id"))
            _logger.info("#### values data list : %s ", values)

            self.do_picking(values=values)
            for record in record_ids:
                TEABLE.update_record_by_id(
                    table_id=table_id,
                    record_id=record,
                    update_fields={"received": "Received"},
                )

            _logger.info("# Picking Data In ")
