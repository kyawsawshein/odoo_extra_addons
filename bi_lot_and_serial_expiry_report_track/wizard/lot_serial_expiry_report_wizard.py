# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime, time, timedelta
from typing import List

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class LotSerialExpiryReportWizard(models.TransientModel):
    _name = "lot.serial.expiry.report.wizard"
    _description = "Lot Serial Expiry Report Wizard"

    product_ids = fields.Many2many("product.product", string="Products")
    lot_serial_ids = fields.Many2many("stock.lot", string="Lot/Serial Number")
    expire_within = fields.Integer(string="Expire Within")
    selection_report = fields.Selection(
        [
            ("product_wise", "By Product Wise"),
            ("lot_wise", "By Lot/Serial Wise"),
        ],
        string="Selection of Report",
        default="product_wise",
    )

    def _get_expiration_domain(self) -> List:
        today = datetime.combine(datetime.today(), time.max)
        today_date = datetime.strftime(today, "%Y-%m-%d")
        days_within = today + timedelta(days=int(self.expire_within))
        return [
            ("expiration_date", "!=", False),
            ("product_qty", ">", 0),
            ("expiration_date", ">", today_date),
            ("expiration_date", "<=", days_within),
        ]

    @api.onchange("selection_report")
    def onchange_lot_serial_wise(self):
        domain = self._get_expiration_domain()
        if self.selection_report == "lot_wise":
            stock_production_lot_obj = self.env["stock.lot"].search(domain)
            self.lot_serial_ids = stock_production_lot_obj
            self.product_ids = False

    def expiration_date(self, rec, product_list: List, today: datetime):
        vals_dict = {
            "lot_serial_number": rec.name,
            "product_name": rec.product_id.name,
            "product_expiry_date": rec.expiration_date.date(),
            "product_expire_within": str(rec.expiration_date.date() - today.date()),
            "product_qty": rec.product_qty,
        }
        product_list.append(vals_dict)

    def action_expiry_report(self):
        product_list = []
        ir_module_module_obj = self.env["ir.module.module"].search(
            [("name", "=", "product_expiry"), ("state", "=", "installed")]
        )

        if ir_module_module_obj:
            today = datetime.today()
            if self.expire_within > 0:
                if self.selection_report == "product_wise":
                    domain = self._get_expiration_domain()
                    domain.append(("product_id", "in", self.product_ids.ids))
                    for rec in self.env["stock.lot"].search(domain):
                        self.expiration_date(rec, product_list, today)

                    if not product_list:
                        raise UserError("No record found for this selected products.")

                if self.selection_report == "lot_wise":
                    domain = self._get_expiration_domain()
                    domain.append(("id", "in", self.lot_serial_ids.ids))
                    for rec in self.env["stock.lot"].search(domain):
                        self.expiration_date(rec, product_list, today)

                    if not product_list:
                        raise UserError(
                            "No record found for this selected lot/Serial numbers."
                        )
            else:
                raise UserError("Please enter positive number.")
        else:
            raise ValidationError("Please Enable Settings --> Expiration Dates Option.")

        data = {"wizard_data": self.read()[0], "product_list": product_list}
        return self.env.ref(
            "bi_lot_and_serial_expiry_report_track.action_lot_and_serial_expiry_report"
        ).report_action(self, data=data)
