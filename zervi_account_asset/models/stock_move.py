# -*- coding: utf-8 -*-

import logging
from collections import defaultdict
from typing import Dict, List

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

from ..datamodels.asset_data import Assets, State

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    # overrided base function
    def _action_done(self, cancel_backorder=False):
        moves = super()._action_done(cancel_backorder=cancel_backorder)
        moves_in = moves.filtered(lambda m: m.is_in)
        moves_out = moves.filtered(lambda m: m.is_out)
        for move in moves_in.filtered(
            lambda m: m.product_id.asset_category_id and m.value > 0
        ):
            move.asset_create()

        for move in moves_out.filtered(
            lambda m: m.product_id.asset_category_id and m.value > 0
        ):
            move.update_assets()

        return moves

    def asset_create(self):
        asset_list = []
        asset_obj = self.env["account.asset.asset"]
        company_id = self.company_id.id
        asset_categ = self.product_id.asset_category_id
        partner_id = self.picking_id.partner_id.id
        categ_vale = asset_obj.onchange_category_id_values(asset_categ.id)
        date = self.date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        for line in self.move_line_ids.filtered(lambda l: l.expiration_date):
            asset = Assets(
                name=line.product_id.name,
                code=line.picking_id.name or False,
                product_id=line.product_id.id,
                quantity=line.quantity,
                category_id=asset_categ.id,
                value=(self.value / self.quantity) * line.quantity,
                partner_id=partner_id,
                company_id=company_id,
                date=date,
                lot_name=line.lot_id.name or line.lot_name,
            ).__dict__
            asset.update(categ_vale["value"])
            asset["method_end"] = line.expiration_date.strftime(
                DEFAULT_SERVER_DATE_FORMAT
            )
            asset_list.append(asset)
        asset_obj.create_asset(asset_list)

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

    def get_assets(self, code: str = None):
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

        if code:
            domain.append(("code", "in", code))

        if lot_names:
            domain.append(("lot_name", "in", lot_names))

        asset_qty = self.product_uom_qty
        _logger.info(f"Asset get domain : {domain}")
        assets = self.env["account.asset.asset"].search(
            domain, limit=asset_qty, order="method_end asc"
        )

        return assets

    def update_assets(self):
        asset_qty = self.quantity or self.product_uom_qty
        assets = self.get_assets()
        if not assets:
            raise UserError(_("No assets found."))

        remove_assets = self.get_remove_value(assets, asset_qty)
        _logger.info(f"Remove assets : {remove_assets}")

        for asset, data in remove_assets.items():
            self.env["account.asset.asset"].browse(asset).write(data)
