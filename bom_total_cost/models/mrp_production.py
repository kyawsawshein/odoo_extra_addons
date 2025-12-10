import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    """Inherit mrp.bom model to add total cost of BOM"""

    _inherit = "mrp.production"

    total_actual_bom_cost = fields.Float(compute="_compute_total_actual_bom_csot")

    @api.depends("bom_id", "product_qty", "workorder_ids")
    def _compute_total_actual_bom_csot(self):
        for production in self:
            raw_cost = 0.0
            for move in self.move_raw_ids:
                company = self.env.company
                price = (
                    move.product_id.uom_id._compute_price(
                        move.product_id.with_company(company).standard_price,
                        move.product_uom,
                    )
                    * move.product_uom_qty
                )
                raw_cost += company.currency_id.round(price)
            production.total_actual_bom_cost = raw_cost

            operation_cost = 0.0
            for workorder in production.workorder_ids:
                _logger.info(f"workorder {workorder.name}")
                operation_cost += workorder._cal_cost()

            _logger.info(f"# operaton cost {operation_cost}")
            production.total_actual_bom_cost += operation_cost
