import logging
from itertools import groupby
from typing import Dict, List

from odoo import _, api, fields, models

from ..datamodels.datamodel import LineData, MoveData, PickingData

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

    def get_expired_lots(self, rule):
        # Get current location of the lot
        company_id = rule.company_id.id
        expired_date = rule.expired_date or fields.Date.today()
        domain = [("expiration_date", "<=", expired_date), ("avg_cost", "<=", 0)]

        _logger.info("# get expired lot doamin %s ", domain)
        expired_lots = self.env["stock.lot"].search(domain)
        quant_domain = [
            ("lot_id", "in", expired_lots.ids),
            ("quantity", ">", 0),
            ("location_id.usage", "=", "internal"),
        ]
        _logger.info("# domain stock quant %s ", quant_domain)
        if company_id:
            quant_domain.append(("company_id", "=", company_id))

        lot_stock_quants = self.env["stock.quant"].search(quant_domain)
        return lot_stock_quants

    @api.model
    def _cron_lot_expired_move(self):
        self.do_transfer()

    @api.model
    def do_transfer(self):
        for rule in self.search([("active", "=", True)]):
            expired_lot_quants = self.get_expired_lots(rule)
            for location, lot_quants in groupby(
                sorted(expired_lot_quants, key=lambda q: q.location_id),
                key=lambda q: q.location_id,
            ):
                _logger.info("# Stock location %s", location.name)
                picking = rule.create_picking(location.id, lot_quants)
                picking.action_assign()
                if rule.validation_picking and picking.state == "assigned":
                    picking.button_validate()

    def add_move_line(self, line, location_id: int, location_dest_id: int):
        return LineData(
            product_id=line.product_id.id,
            product_uom_id=line.product_id.uom_id.id,
            location_id=location_id,
            location_dest_id=location_dest_id,
            lot_id=line.lot_id.id,
            quantity=line.quantity,
        ).__dict__

    def _prepare_move(self, line, location_id, location_dest_id) -> Dict:
        move = MoveData(
            location_id=location_id,
            location_dest_id=location_dest_id,
            product_id=line.product_id.id,
            product_uom=line.product_uom_id.id,
            product_uom_qty=line.quantity,
            price_unit=line.lot_id.standard_price,
            move_line_ids=[
                (0, 0, self.add_move_line(line, location_id, location_dest_id))
            ],
        ).__dict__

        return move

    def add_move(self, lot_quants, location_id, location_dest_id) -> List:
        moves = []
        for quant in lot_quants:
            moves.append(
                (
                    0,
                    0,
                    self._prepare_move(
                        line=quant,
                        location_id=location_id,
                        location_dest_id=location_dest_id,
                    ),
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
