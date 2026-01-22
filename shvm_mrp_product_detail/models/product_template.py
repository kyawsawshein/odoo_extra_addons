from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    production_ids = fields.One2many("mrp.production", "product_tmpl_id")
