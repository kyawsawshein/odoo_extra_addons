import logging
from typing import Dict

from odoo import _, fields, models

VALUATION_DICT = {
    "value": 0,
    "quantity": 0,
    "description": False,
}


_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    uom_conversion_id = fields.Many2one("uom.conversion", string="UOM Conversion")

    def _get_value_from_uom_conversion(self, quantity: float, at_date=None) -> Dict:
        if self.uom_conversion_id and self.is_in:
            return {
                "value": self.price_unit * self.quantity,
                "quantity": quantity,
                "description": _(
                    "Value based on simple mrp move %(reference)s",
                    reference=self.reference,
                ),
            }
        return dict(VALUATION_DICT)

    # overrided function
    def _get_value_data(
        self,
        forced_std_price=False,
        at_date=False,
        ignore_manual_update=False,
        add_extra_value=True,
    ):
        res = super()._get_value_data(
            forced_std_price, at_date, ignore_manual_update, add_extra_value
        )
        if self.uom_conversion_id and self.is_in:
            res.update(self._get_value_from_uom_conversion(self.quantity))

        return res
