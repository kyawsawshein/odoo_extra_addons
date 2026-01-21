from typing import List, Dict
from collections import defaultdict
from odoo import models


class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    def get_asset_update_value(self, assets: List, value: float, update_assets: Dict):
        for asset in assets:
            value = asset.value + value
            update_assets[asset.id] = {
                "value": value,
            }

    def button_validate(self):
        res = super().button_validate()
        update_assets = defaultdict(dict)
        for cost in self:
            cost = cost.with_company(cost.company_id)
            pickings = cost.picking_ids
            for line in cost.valuation_adjustment_lines.filtered(
                lambda line: line.move_id
            ):
                product = line.move_id.product_id
                if product.valuation != "real_time":
                    continue
                asset = line.move_id.get_assets(code=pickings.mapped("name"))
                self.get_asset_update_value(
                    assets=asset,
                    value=line.additional_landed_cost,
                    update_assets=update_assets,
                )

        for asset, data in update_assets.items():
            self.env["account.asset.asset"].browse(asset).write(data)

        return res
