from odoo import api, fields, models

from .product_product import PRODUCT_GRADE


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_grade = fields.Selection(
        selection=PRODUCT_GRADE,
        string="Product Grade",
        compute="_compute_product_grade",
        inverse="_inverse_product_grade",
        help="Product Condition.",
        store=True,
    )

    @api.depends("product_variant_ids.product_grade")
    def _compute_product_grade(self):
        self._compute_template_field_from_variant_field("product_grade")

    def _inverse_product_grade(self):
        self._set_product_variant_field("product_grade")
