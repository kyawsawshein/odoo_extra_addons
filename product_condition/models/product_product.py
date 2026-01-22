from odoo import api, fields, models

from ..datamodels.datamodel import ProductGrade

PRODUCT_GRADE = [
    ("ga", "Grade A"),
    ("gb", "Grade B"),
    ("gc", "Grade C"),
]


class ProductProduct(models.Model):
    _inherit = "product.product"

    product_grade = fields.Selection(
        selection=ProductGrade.get_list(),
        string="Grade",
        help="Product grade.",
        default="ga",
    )


class StockLot(models.Model):
    _inherit = "stock.lot"

    grade = fields.Selection(
        selection=ProductGrade.get_list(),
        string="Grade",
        help="Product grade.",
        default="ga",
    )

    @api.onchange("product_expiry_alert")
    def _onchange_expiry(self):
        """Compute totals of multiple svl related values"""
        for lot in self:
            if lot.product_expiry_alert:
                lot.grade = ProductGrade.GB.code
