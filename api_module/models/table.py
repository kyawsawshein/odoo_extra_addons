import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

import requests

# teable_accT5fdyermOdrlIf1p_Ikw0wSYqrGWmrvqlAhQjTP+b04Xf+RvWr/ntjqwG14w=


# url = "https://app.teable.ai/api/table/tblZR5DYQzflyJdCkPQ/record"
# params = {
#     "fieldKeyType": "dbFieldName",
#     "filter": json.dumps(
#         {
#             "conjunction": "and",
#             "filterSet": [
#                 {"fieldId": "Status1771906092278", "operator": "is", "value": "done"}
#             ],
#         }
#     ),
#     "orderBy": json.dumps([{"fieldId": "Label", "order": "asc"}]),
#     "cellFormat": "json",
# }

# headers = {
#     "Authorization": "Bearer teable_accT5fdyermOdrlIf1p_Ikw0wSYqrGWmrvqlAhQjTP+b04Xf+RvWr/ntjqwG14w=",
#     "Accept": "application/json",
# }

# response = requests.get(url, params=params, headers=headers)
# # print(response.json())


@dataclass
class FGProduction:
    po_no: str
    unit: str
    mo_no: str
    Type_BOX: str
    inv_no: str
    n_v: str
    g_w: str
    b_w: str
    qty: str
    status: str
    product: str
    lot_name: str
    product_code: str
    order_date: str = ""
    invoice_date: str = ""
    delivery_date: str = ""
    so_no: str = ""
    price: float = 0.0
    amount: float = 0.0
    create_date: str = ""
    create_by: str = ""
    write_date: str = ""
    write_by: str = ""

    def __post_init__(self):
        if isinstance(self.mo_no, dict):
            self.mo_no = self.mo_no.get("title")


# for key, values in response.json().items():
#     for val in values if key == "records" else []:
#         # print(val.get("fields"))
#         data = FGProduction(**val.get("fields"))
#         print(data)


from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ...data_commom.datamodels.datamodel import (
    LineData,
    MoveData,
    PickingData,
    default_ids,
)

_logger = logging.getLogger(__name__)


class Table(models.Model):

    def get_connection_table(self):
        _logger.info("API fetch data from table")
        url = "https://app.teable.ai/api/table/tblZR5DYQzflyJdCkPQ/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps(
                {
                    "conjunction": "and",
                    "filterSet": [
                        {
                            "fieldId": "Status1771906092278",
                            "operator": "is",
                            "value": "done",
                        }
                    ],
                }
            ),
            "orderBy": json.dumps([{"fieldId": "po_no", "order": "asc"}]),
            "cellFormat": "json",
        }

        headers = {
            "Authorization": "Bearer teable_accT5fdyermOdrlIf1p_Ikw0wSYqrGWmrvqlAhQjTP+b04Xf+RvWr/ntjqwG14w=",
            "Accept": "application/json",
        }

        response = requests.get(url, params=params, headers=headers)
        # _logger.info("Data response %s ", response)
        return response

    def get_production_data(self) -> List:
        _logger.info("get produciton data from table...")
        data_list = []
        response = self.get_connection_table()

        for key, values in response.json().items():
            for val in values if key == "records" else []:
                _logger.info("val %s ", val)
                data = FGProduction(**val.get("fields"))
                data_list.append(data)
        _logger.info("Production data model list %s ", data_list)
        return data_list

    def add_move_line(
        self,
        line,
        product,
        picking: PickingData,
    ) -> LineData:
        return LineData(
            product_id=product.id,
            product_uom_id=product.uom_id.id,
            location_id=picking.location_id,
            location_dest_id=picking.location_dest_id,
            quantity=line.quantity,
            lot_name=line.lot_name,
        )

    def add_move(self, line, product, picking: PickingData) -> MoveData:
        return MoveData(
            location_id=picking.location_id,
            location_dest_id=picking.location_dest_id,
            product_id=product.id,
            product_uom=product.uom_id.id,
            product_uom_qty=line.quantity,
            price_unit=line.price_unit,
        )

    def _prepare_move_in(self, lines, picking: PickingData) -> List:
        moves = []
        for line in lines:
            product = self.env["product.product"].search(
                [("default_code", "=", line.product_code)]
            )
            move = self.add_move(line, product, picking)
            move.picking_type_id = picking.picking_type_id
            move.move_line_ids = [
                default_ids(
                    self.add_move_line(
                        line,
                        product,
                        picking,
                    ),
                )
            ]
            moves.append(default_ids(move))
        return moves

    def prepare_picking(
        self, picking_type_id: int, location_id: int, location_dest_id: int
    ) -> PickingData:
        picking = PickingData(
            picking_type_id=picking_type_id,
            location_id=location_id,
            location_dest_id=location_dest_id,
            date_done=fields.Datetime.now(),
        )
        return picking

    def create_picking_lines_in(self, context: Dict, data: List[FGProduction]):
        picking_type = self.env["stock.picking.type"].browse([1])
        location_id = picking_type.default_location_src_id.id
        location_dest_id = 5
        picking_data = self.prepare_picking(
            picking_type_id=1,
            location_id=location_id,
            location_dest_id=location_dest_id,
        )
        moves = self._prepare_move_in(
            lines=data,
            picking=picking_data,
        )
        picking_data.move_ids = moves
        _logger.info("# Picking Data In : %s ", picking_data)
        return (
            self.env["stock.picking"]
            .with_context(**context)
            .create(picking_data.__dict__)
        )

    def table_receive(self):
        # picking_type_receipt_production = self.picking_type_receipt_production
        _logger.info("Start receiving form table ....")
        context_in = {"default_picking_type_id": 1}
        data_list = self.get_production_data()
        picking_in = self.create_picking_lines_in(context_in, data_list)

        # se face receptia
        if picking_in.move_ids:
            picking_in.action_assign()
            if picking_in.state == "assigned":
                picking_in.button_validate()
        _logger.info("Done validaet picking for in.")

        self.write({"state": "done"})
        return self
