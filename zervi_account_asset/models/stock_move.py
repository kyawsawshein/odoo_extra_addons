# -*- coding: utf-8 -*-

import logging
from collections import defaultdict
from typing import Dict, List

from odoo import _, models
from odoo.exceptions import UserError
from odoo.fields import Domain
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

from ..datamodels.asset_data import Assets, State

_logger = logging.getLogger(__name__)

VALUATION_DICT = {
    "value": 0,
    "quantity": 0,
    "description": False,
}


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_manual_value(self, quantity: float, at_date=None):
        valuation_data = dict(VALUATION_DICT)
        domain = Domain([("move_id", "=", self.id)])
        if at_date:
            domain &= Domain([("date", "<=", at_date)])
        manual_value = self.env["product.value"].search(
            domain, order="date desc, id desc", limit=1
        )
        if manual_value:
            valuation_data["value"] = (
                manual_value.value * manual_value.lot_id.product_qty
                if manual_value.lot_id
                else manual_value.value
            )
            valuation_data["quantity"] = quantity
            description = _(
                "Adjusted on %(date)s by %(user)s",
                date=manual_value.date,
                user=manual_value.user_id.name,
            )
            if manual_value.description:
                description += "\n" + manual_value.description
            valuation_data["description"] = description
        return valuation_data

    # overrided base function
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
        vals = []
        asset_categ = self.product_id.asset_category_id
        lines = self.move_line_ids

        if asset_categ and lines[:1].expiration_date:
            end_date = lines[:1].expiration_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            vals.append(
                Assets(
                    name=self.product_id.name,
                    code=self.picking_id.name or False,
                    product_id=self.product_id.id,
                    quantity=self.quantity,
                    category_id=asset_categ.id,
                    value=self.value,
                    partner_id=self.picking_id.partner_id.id,
                    company_id=self.company_id.id,
                    date=self.date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    lot_name=lines[:1].lot_name,
                ).__dict__
            )
            self.env["account.asset.asset"].create_asset(vals, end_date)

    def get_remove_value(self, assets: List, asset_qty: float) -> Dict:
        remove_assets = defaultdict(dict)
        for asset in assets:
            remove_qty = min(asset.quantity, asset_qty)
            salvage_value = asset.salvage_value + (
                (asset.value_residual / asset.quantity) * remove_qty
            )
            remove_assets[asset.id] = {
                "quantity": asset.quantity - self.quantity,
                "salvage_value": salvage_value,
            }
            asset_qty -= remove_qty
            if asset_qty <= 0:
                break

        if asset_qty > 0:
            raise UserError(_("Not enough assets found."))
        return remove_assets

    def update_assets(self):
        lot_names = []
        for line in self.move_line_ids:
            if line.lot_id:
                lot_names.append(line.lot_id.name)

        domain = [
            ("product_id", "=", self.product_id.id),
            ("state", "=", State.OPEN.code),
            ("category_id", "=", self.product_id.asset_category_id.id),
            ("quantity", ">", 0),
        ]

        if lot_names:
            domain.append(("lot_name", "in", lot_names))

        asset_qty = self.product_uom_qty
        _logger.info(f"Asset get domain : {domain}")
        assets = self.env["account.asset.asset"].search(
            domain, limit=asset_qty, order="method_end asc"
        )
        if not assets:
            raise UserError(_("No assets found."))

        remove_assets = self.get_remove_value(assets, asset_qty)
        _logger.info(f"Remove assets : {remove_assets}")

        for asset, data in remove_assets.items():
            self.env["account.asset.asset"].browse(asset).write(data)
