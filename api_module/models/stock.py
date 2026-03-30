import logging
from typing import Dict, List

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ...data_commom.datamodels.datamodel import (
    LineData,
    MoveData,
    PickingData,
    default_ids,
)
from ..helper.teable_endpoint import TeableAPIClient

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    # def add_move_line(self, value) -> LineData:
    #     return LineData(
    #         product_id=value.get("product_id"),
    #         product_uom_id=value.get("uom_id"),
    #         location_id=1,
    #         location_dest_id=5,
    #         quantity=value.get("quantity"),
    #         lot_name=value.get("lot_name"),
    #     )

    # def add_move(self, value) -> MoveData:
    #     return MoveData(
    #         location_id=1,
    #         location_dest_id=5,
    #         product_id=value.get("product_id"),
    #         product_uom=value.get("uom_id"),
    #         product_uom_qty=value.get("quantity"),
    #         price_unit=value.get("price"),
    #     )

    # def _prepare_move_in(self, value, picking) -> Dict:
    #     moves = []
    #     move = self.add_move(value)
    #     move.move_line_ids = [default_ids(self.add_move_line(value))]
    #     return move.to_dict()

    def do_receive(self, value: Dict):
        value = {
            "location_id": 1,
            "location_dest_id": 5,
            "product_id": 115447,
            "product_uom": 1,
            "product_uom_qty": 5,
            "move_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": 115447,
                        "product_uom_id": 1,
                        "location_id": 1,
                        "location_dest_id": 5,
                        "quantity": 5,
                        "lot_id": None,
                        "lot_name": "WH/MO/00067-1",
                        "move_id": None,
                    },
                )
            ],
            "state": "confirmed",
        }

        move_data = self._prepare_move_in(value)
        # se face receptia
        move = self.create(move_data)
        move._action_assign()
        move.action_done()

        _logger.info("Done create stock move in.")
        return move

    def add_move_line(
        self,
        line,
        picking: PickingData,
        qty: float,
        lot_id: int = None,
        lot_name: str = "",
    ) -> LineData:
        return LineData(
            product_id=line.get("product_id"),
            product_uom_id=line.get("uom_id"),
            location_id=picking.location_id,
            location_dest_id=picking.location_dest_id,
            lot_id=lot_id,
            quantity=qty,
            lot_name=lot_name,
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

    def _prepare_move_in(self, lines, picking: PickingData) -> List:
        moves = []
        for line in lines:
            _logger.info("### Line : %s", line)
            move = self.add_move(line, picking)
            move.picking_type_id = picking.picking_type_id
            move.move_line_ids = [
                default_ids(
                    self.add_move_line(
                        line,
                        picking,
                        qty=line.get("quantity"),
                        lot_name=line.get("lot_name"),
                    ),
                )
            ]
            moves.append(default_ids(move))
        return moves

    def prepare_picking(
        self,
        picking_type_id: int,
        location_id: int = None,
        location_dest_id: int = None,
    ) -> PickingData:
        picking = PickingData(
            picking_type_id=picking_type_id,
            location_id=1,
            location_dest_id=5,
            date_done=fields.Datetime.now(),
        )
        return picking

    def create_picking_lines_in(self, context: Dict, values: Dict):
        # location_id = picking_type.default_location_src_id.id
        # location_dest_id = self.location_dest_id.id
        picking_data = self.prepare_picking(
            picking_type_id=1,
            location_id=0,
            location_dest_id=0,
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

    def do_picking(self, values: Dict):
        context_in = {"default_picking_type_id": 1}
        picking_data = self.prepare_picking(
            picking_type_id=1,
            location_id=0,
            location_dest_id=0,
        )

        picking_in = self.create_picking_lines_in(context_in, values)

        # se face receptia
        if picking_in.move_ids:
            picking_in.action_assign()
            if self.validation_receipt and picking_in.state == "assigned":
                picking_in.button_validate()

        _logger.info("Done validaet picking for in.")

    def add_picking_line(self, picking, product, quantity, uom, price_unit):
        move = self.env["stock.move"].search(
            [
                ("picking_id", "=", picking.id),
                ("product_id", "=", product.id),
                ("product_uom", "=", uom.id),
            ]
        )
        if move:
            qty = move.product_uom_qty + quantity
            move.write({"product_uom_qty": qty})
        else:
            values = {
                "state": "confirmed",
                "product_id": product.id,
                "product_uom": uom.id,
                "product_uom_qty": quantity,
                # 'quantity_done': quantity,  # o fi bine >???
                "picking_id": picking.id,
                "price_unit": price_unit,
                "location_id": picking.picking_type_id.default_location_src_id.id,
                "location_dest_id": picking.picking_type_id.default_location_dest_id.id,
                "picking_type_id": picking.picking_type_id.id,
            }

            move = self.env["stock.move"].create(values)
        return move

    def sync_teab_finished_goods(self):
        table = "mo_finished_goods"
        api = self.env["api.config"].search([("name", "=", "Teable AI")])
        client = TeableAPIClient(database=api.database, api_token=api.token_key)
        filter_list = [
            {"fieldId": "Status", "operator": "is", "value": "Done"},
        ]
        sort_list = [{"fieldId": "ID", "order": "asc"}]
        finished_goods = client.get_records(table, filter_list, sort_list)

        context = {"default_picking_type_id": 1}
        picking_data = self.prepare_picking(
            picking_type_id=1,
            location_id=0,
            location_dest_id=0,
        )

        values = []
        for goods in finished_goods:
            _logger.info("==================== finished goods %s", goods.get("fields"))
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
        _logger.info("#### values data list : %s ", values)
        moves = self._prepare_move_in(
            lines=values,
            picking=picking_data,
        )
        picking_data.move_ids = moves
        _logger.info("# Picking Data In : %s ", picking_data)
        picking_in = (
            self.env["stock.picking"]
            .with_context(**context)
            .create(picking_data.__dict__)
        )

        if picking_in.move_ids:
            picking_in.action_assign()
            if picking_in.state == "assigned":
                picking_in.button_validate()
