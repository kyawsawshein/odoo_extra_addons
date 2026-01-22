from odoo import fields, models


class ProductVariants(models.Model):
    _inherit = "product.product"

    production_ids = fields.One2many("mrp.production", "product_id")
