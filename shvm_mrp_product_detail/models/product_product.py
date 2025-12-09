# -*- coding: utf-8 -*-
# Email: sales@creyox.com

from odoo import _, api, fields, models


class ProductVariants(models.Model):
    _inherit = "product.product"

    production_ids = fields.One2many("mrp.production", "product_id")
