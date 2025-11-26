import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # pylint: disable=W0201
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get("create_bill"):
            if (
                self.product_id
                and self.move_id.move_type == "out_invoice"
                and self.product_id.product_tmpl_id.deferred_revenue_category_id
            ):
                self.asset_category_id = (
                    self.product_id.product_tmpl_id.deferred_revenue_category_id.id
                )
            elif self.product_id and self.move_id.move_type == "in_invoice":
                self.asset_category_id = None
            self.onchange_asset_category_id()

        return res

    @api.onchange("product_id")
    def _inverse_product_id(self):
        res = super()._inverse_product_id()
        for rec in self:
            if rec.product_id:
                if rec.move_id.move_type == "out_invoice":
                    rec.asset_category_id = (
                        rec.product_id.product_tmpl_id.deferred_revenue_category_id.id
                    )
                elif rec.move_id.move_type == "in_invoice":
                    rec.asset_category_id = None
        return res
