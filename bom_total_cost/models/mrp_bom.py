# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(Contact : odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class MrpBom(models.Model):
    """Inherit mrp.bom model to add total cost of BOM"""

    _inherit = "mrp.bom"

    currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Currency",
        help="The currency used by the company",
    )
    bom_cost = fields.Monetary(
        string="Cost Per Unit",
        compute="_compute_bom_cost",
        currency_field="currency_id",
        help="Total cost of the BOM based on the raw\n"
        " materials cost price per unit",
    )
    total_bom_cost = fields.Monetary(
        string="Total Cost",
        compute="_compute_bom_cost",
        currency_field="currency_id",
        help="Total cost of the BOM based on the\n" " raw materials cost",
    )
    operation_cost = fields.Monetary(
        string="Operatin Cost",
        compute="_compute_bom_cost",
        currency_field="currency_id",
        help="Total cost of the operation.",
    )

    @api.depends("bom_line_ids.product_id", "product_qty")
    def _compute_bom_cost(self):
        """Compute total cost per unit"""
        for rec in self:
            cost_mapp = rec.bom_line_ids.mapped("cost")
            rec.bom_cost = sum(cost_mapp)

            product = self.product_id or self.product_tmpl_id.product_variant_id
            qty = self.product_qty
            for operation in self.operation_ids:
                if not product or operation._skip_operation_line(product):
                    continue
                op = operation.with_context(product=product, quantity=qty)
                rec.operation_cost += self.env.company.currency_id.round(op.cost)

            rec.total_bom_cost = (rec.bom_cost + rec.operation_cost) * rec.product_qty
            rec.total_bom_cost += self.total_material_cost
            rec.total_bom_cost += self.total_labour_cost
            rec.total_bom_cost += self.total_overhead_cost
