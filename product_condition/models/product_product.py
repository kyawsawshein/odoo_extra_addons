from odoo import fields, models

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

    grade = fields.Selection(selection=ProductGrade.get_list(),
        string="Grade",
        help="Product grade.",
        default="ga",)
