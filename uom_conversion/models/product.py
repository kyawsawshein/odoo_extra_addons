from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    raw_product_id = fields.Many2one(
        comodel_name="product.product", string="Raw Product"
    )
