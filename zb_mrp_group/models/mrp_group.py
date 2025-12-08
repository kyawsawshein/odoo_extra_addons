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
from random import randint


class MrpGroup(models.Model):
    _name = "mrp.group"
    _rec_name = "name"
    _inherit = ["mail.thread"]
    _description = "Mrp Group"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string="Name", tracking=True)
    color = fields.Integer(string="Color", default=_get_default_color)

    _sql_constraints = [("unique_name", "unique(name)", "Group name should be unique!")]
