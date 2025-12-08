# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2024 ZestyBeanz Technologies(<http://www.zbeanztech.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models, _


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    mrp_group_ids = fields.Many2many("mrp.group", string="MRP Groups")

    @api.onchange("bom_id")
    def _onchange_bom(self):
        for rec in self:
            if rec.bom_id:
                rec.mrp_group_ids = rec.bom_id.mrp_group_ids
