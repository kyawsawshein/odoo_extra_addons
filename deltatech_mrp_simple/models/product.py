
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    raw_product_id = fields.Many2one(comodel_name="product.template", string="Raw Product")
