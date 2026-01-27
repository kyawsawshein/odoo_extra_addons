import logging
from datetime import datetime, time
from itertools import groupby
from typing import Dict, List

from odoo import _, api, fields, models

from ...data_commom.datamodels.datamodel import default_ids
from ...data_commom.datamodels.datamodel import LineData, MoveData, PickingData
from ..datamodels.datamodel import LocationType
from ..helpers.query import ExpCols, Query

_logger = logging.getLogger(__name__)


class LotDepreciation(models.Model):
    _name = "lot.expiration"
    _description = "Lot Expiration"

    name = fields.Char()
    active = fields.Boolean(
        "Active",
        default=True,
        help="If unchecked, it will allow you to hide the rule without removing it.",
    )
    sequence = fields.Integer("Sequence", default=20)
    picking_type_id = fields.Many2one(
        "stock.picking.type",
        "Operation Type",
        required=True,
        check_company=True,
        domain="[('code', 'in', ('internal'))]",
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    location_src_id = fields.Many2one(
        "stock.location", "Source Location", check_company=True, index=True
    )
    location_dest_id = fields.Many2one(
        "stock.location",
        "Destination Location",
        required=True,
        check_company=True,
        domain="[('usage', 'in', ('inventory'))]",
    )
    validation_picking = fields.Boolean(default=True)
    picking_type_code_domain = fields.Json(compute="_compute_picking_type_code_domain")
    expired_date = fields.Date()

    def _compute_picking_type_code_domain(self):
        self.picking_type_code_domain = [("code", "in", ("internal"))]

    def _build_query(self, rule) -> str:
        company = rule.company_id
        expired_date = rule.expired_date or fields.Date.today()
        query = Query.get_lot_expiration.format(
            company_id=company.id,
            location_type=(LocationType.INTERNAL.code, LocationType.TRANSIT.code),
            lot_valuated=True,
            expiration_date=datetime.combine(expired_date, time.max),
        )
        return query

    def get_expired_lots(self, rule) -> List:
        # Get current location of the lot
        self.env.cr.execute(self._build_query(rule=rule))
        return self.env.cr.fetchall()

    @api.model
    def _cron_lot_expired_move(self):
        self.do_transfer()

    @api.model
    def do_transfer(self):
        for rule in self.search([("active", "=", True)]):
            expired_lot = self.get_expired_lots(rule)
            for location, lot_quants in groupby(
                sorted(expired_lot, key=lambda q: q[ExpCols.LOCATION]),
                key=lambda q: q[ExpCols.LOCATION],
            ):
                picking = rule.create_picking(location, lot_quants)
                picking.action_assign()
                _logger.info("# Picking Internal trasfer %s ", picking)
                if rule.validation_picking and picking.state == "assigned":
                    picking.button_validate()

    def add_move_line(self, line, location_id: int, location_dest_id: int) -> LineData:
        return LineData(
            product_id=line[ExpCols.PRODUCT_ID],
            product_uom_id=line[ExpCols.UOM_ID],
            location_id=location_id,
            location_dest_id=location_dest_id,
            lot_id=line[ExpCols.LOT_ID],
            quantity=line[ExpCols.QUANTITY],
        )

    def _prepare_move(self, line, location_id, location_dest_id) -> MoveData:
        move = MoveData(
            location_id=location_id,
            location_dest_id=location_dest_id,
            product_id=line[ExpCols.PRODUCT_ID],
            product_uom=line[ExpCols.UOM_ID],
            product_uom_qty=line[ExpCols.QUANTITY],
            price_unit=line[ExpCols.AVG_COST],
            move_line_ids=[
                default_ids(self.add_move_line(line, location_id, location_dest_id))
            ],
        )

        return move

    def add_move(self, lot_quants, location_id, location_dest_id) -> List:
        moves = []
        for quant in lot_quants:
            moves.append(
                default_ids(
                    self._prepare_move(
                        line=quant,
                        location_id=location_id,
                        location_dest_id=location_dest_id,
                    )
                )
            )
        return moves

    def create_picking(self, location_id: int, lot_quants: list):
        location_dest_id = self.location_dest_id.id
        picking = PickingData(
            picking_type_id=self.picking_type_id.id,
            location_id=location_id,
            location_dest_id=self.location_dest_id.id,
            date_done=fields.Datetime.now(),
            move_ids=self.add_move(lot_quants, location_id, location_dest_id),
        )
        _logger.info("## Picking data %s ", picking)
        return self.env["stock.picking"].create(picking.__dict__)
