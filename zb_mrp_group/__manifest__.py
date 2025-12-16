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
{
    "name": "MRP Group",
    "version": "19.0.0.0",
    "category": "Manufacturing",
    "summary": "This module simplifies production management by organizing BOMs and MOs into groups,"
    " streamlining complex production processes. It helps identify and group multiple BOMs and"
    "MOs involved in producing a finished product, making production management more efficient.",
    "website": "https://www.zbeanztech.com",
    "description": """
        This app will allow you to manage Manufacturing Group on "Manufacturing Order"..
        """,
    "author": "ZestyBeanz Technologies",
    "maintainer": "ZestyBeanz Technologies",
    "support": "support@zbeanztech.com",
    "license": "LGPL-3",
    "icon": "/zb_mrp_group/static/description/icon.png",
    "images": [
        "static/description/banners/banner.png",
    ],
    "currency": "USD",
    "price": 0.0,
    "depends": [
        "mrp",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/mrp_bom_view.xml",
        "views/mrp_group_view.xml",
        "views/mrp_production_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
