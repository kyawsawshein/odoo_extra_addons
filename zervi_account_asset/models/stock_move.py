# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from collections import defaultdict

from odoo import models
from odoo.exceptions import UserError
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

from ..datamodels.asset_data import Assets

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        moves = super()._action_done(cancel_backorder=cancel_backorder)
        moves_in = moves.filtered(lambda m: m.is_in)
        moves_out = moves.filtered(lambda m: m.is_out)
        for move in moves_in.filtered(lambda m: m.product_id.asset_category_id):
            move.asset_create()

        for move in moves_out.filtered(lambda m: m.product_id.asset_category_id):
            move.update_assets()

        return moves

    def asset_create(self):
        asset_categ = self.product_id.asset_category_id
        lines = self.move_line_ids
        vals = Assets(
            name=self.product_id.name,
            code=self.picking_id.name or False,
            product_id=self.product_id.id,
            quantity=self.quantity,
            category_id=asset_categ.id,
            value=self.value,
            partner_id=self.picking_id.partner_id.id,
            company_id=self.company_id.id,
            date=self.date.strftime(DEFAULT_SERVER_DATE_FORMAT),
            date_first_depreciation="last_day_period",
            method_end=lines[:1].expiration_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
            method_time="end",
        ).__dict__
        changed_vals = self.env["account.asset.asset"].onchange_category_id_values(
            vals["category_id"]
        )
        vals.update(changed_vals["value"])
        asset = self.env["account.asset.asset"].create(vals)
        if asset_categ.open_asset:
            if asset.date_first_depreciation == "last_day_period":
                asset.method_end = lines[:1].expiration_date.date()
            asset.validate()
        return True

    def update_assets(self):
        expiry_date = max(self.move_line_ids.mapped("expiration_date"))
        _logger.info(f"Expiry Date {expiry_date}")
        domain = [
            ("product_id", "=", self.product_id.id),
            ("state", "=", "open"),
            ("type", "=", "purchase"),
            ("category_id", "=", self.product_id.asset_category_id.id),
            ("quantity", ">", 0),
        ]
        if expiry_date:
            domain.append(
                ("method_end", "<=", expiry_date.strftime(DEFAULT_SERVER_DATE_FORMAT))
            )
        asset_qty = self.product_uom_qty
        _logger.info(f"Asset get domain : {domain}")
        assets = self.env["account.asset.asset"].search(
            domain, limit=asset_qty, order="method_end desc"
        )
        if not assets:
            raise UserError(_("No assets found."))

        remove_assets = defaultdict(dict)
        for asset in assets:
            remove_qty = min(asset.quantity, asset_qty)
            salvage_value = (asset.value / asset.quantity) * remove_qty
            remove_assets[asset.id] = {
                "quantity": asset.quantity - self.quantity,
                "salvage_value": salvage_value,
            }
            asset_qty -= remove_qty
            if asset_qty <= 0:
                break

        if asset_qty > 0:
            raise UserError(_("Not enough assets found."))

        _logger.info(f"Remove assets : {remove_assets}")
        for asset, data in remove_assets.items():
            self.env["account.asset.asset"].browse(asset).write(data)
