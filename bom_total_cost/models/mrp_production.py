import logging


from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    """Inherit mrp.bom model to add total cost of BOM"""

    _inherit = "mrp.production"

    total_bom_cost = fields.Float(compute="_compute_bom_total_csot")

    @api.depends("bom_id")
    def _compute_bom_total_csot(self):
        for production in self:
            if production.bom_id:
                production.total_bom_cost = production.bom_id.total_bom_cost
            elif not production.bom_id:
                cost = 0.0
                for move in self.move_raw_ids:
                    company = self.env.company
                    price = (
                        move.product_id.uom_id._compute_price(
                            move.product_id.with_company(company).standard_price,
                            move.product_uom,
                        )
                        * move.product_uom_qty
                    )
                    cost += company.currency_id.round(price)
                production.total_bom_cost = cost

                product = (
                    production.product_id
                    or production.product_tmpl_id.product_variant_id
                )
                qty = production.product_qty
                operation_cost = 0.0
                for workorder in production.workorder_ids:
                    _logger.info(f"workorder {workorder}")
                    for operation in workorder.operation_id:
                        _logger.info(f"operation {operation}")
                        if operation._skip_operation_line(product):
                            continue
                        op = workorder.operation_id.with_context(
                            product=product, quantity=qty
                        )
                        _logger.info(f"operation cost {op.cost}")
                        operation_cost += self.env.company.currency_id.round(op.cost)
                _logger.info(f"# operaton cost {operation_cost}")
                production.total_bom_cost += operation_cost
