import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


# In your custom module's product.py
class ProductProduct(models.Model):
    _inherit = "product.product"

    def _run_fifo(self, quantity, lot=None, at_date=None, location=None):
        # First, get the standard FIFO cost from Odoo's original method.
        fifo_cost = super()._run_fifo(
            quantity, lot=lot, at_date=at_date, location=location
        )

        # If a lot is specified, look for our custom adjustments.
        if lot:
            # Find all adjustments for this lot.
            domain = [("lot_id", "=", lot.id)]
            if at_date:
                domain.append(("date", "<=", at_date))

            adjustments = self.env["product.value"].search(
                domain, order="date desc", limit=1
            )
            if adjustments:
                total_adjustment = adjustments.value * adjustments.lot_id.product_qty

                # Apply the adjustment to the final cost.
                fifo_cost = total_adjustment
                _logger.info("adjustments _run_fifo %s ", fifo_cost)

        return fifo_cost
