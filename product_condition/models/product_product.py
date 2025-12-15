from odoo import fields, models

PRODUCT_GRADE = [
    ("ga", "Grade A"),
    ("gb", "Grade B"),
    ("gc", "Grade C"),
]


class ProductProduct(models.Model):
    _inherit = "product.product"

    product_grade = fields.Selection(
        selection=PRODUCT_GRADE,
        string="Grade",
        help="Product grade.",
        default="ga",
    )
