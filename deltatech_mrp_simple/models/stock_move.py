import logging

from odoo import _, fields, models

VALUATION_DICT = {
    "value": 0,
    "quantity": 0,
    "description": False,
}


_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    simple_mrp_id = fields.Many2one("mrp.simple", string="MRP Simple")

    def _get_value_from_simple_mrp(self, quantity, at_date=None):
        if self.simple_mrp_id and self.is_in:
            return {
                "value": self.price_unit * self.quantity,
                "quantity": quantity,
                "description": _(
                    "Value based on simple mrp move %(reference)s",
                    reference=self.reference,
                ),
            }
        return dict(VALUATION_DICT)

    def _get_value_data(
        self,
        forced_std_price=False,
        at_date=False,
        ignore_manual_update=False,
        add_extra_value=True,
    ):
        _logger.info("Get simple mrp value")
        res = super()._get_value_data(
            forced_std_price, at_date, ignore_manual_update, add_extra_value
        )
        if self.simple_mrp_id and self.is_in:
            res.update(self._get_value_from_simple_mrp(self.quantity))
        _logger.info("# get value data %s", res)
        return res
