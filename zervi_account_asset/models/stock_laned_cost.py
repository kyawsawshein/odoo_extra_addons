import logging
from collections import defaultdict
from typing import Dict

from odoo import models

_logger = logging


class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    def get_asset_update_value(self, adj_line: models.Model, update_assets: Dict):
        move = adj_line.move_id
        cost = adj_line.additional_landed_cost / move.quantity

        for asset in move.get_assets(code=move.picking_id.name):
            value = asset.value + (cost * asset.quantity)
            update_assets[asset.id] = {"value": value}

    def button_validate(self):
        res = super().button_validate()
        update_assets = defaultdict(dict)
        for cost in self:
            cost = cost.with_company(cost.company_id)
            for adj_line in cost.valuation_adjustment_lines.filtered(
                lambda line: line.move_id
            ):
                product = adj_line.move_id.product_id
                if product.valuation != "real_time":
                    continue

                self.get_asset_update_value(
                    adj_line=adj_line, update_assets=update_assets
                )
        _logger.info("Update value adjustment cost for assets %s ", update_assets)
        for asset, data in update_assets.items():
            self.env["account.asset.asset"].browse(asset).write(data)

        return res
