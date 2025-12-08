# pylint: disable = (protected-access)

import logging
from collections import defaultdict
from datetime import date, datetime
from itertools import groupby
from typing import Dict, List

from odoo import _, api, fields, models

from ..datamodels.product_data import ProductValue

_logger = logging.getLogger(__name__)


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Float(string="Quantity")

    def create_asset(self, vals: List[Dict], end_date: str = None):
        for val in vals:
            changed_vals = self.onchange_category_id_values(val["category_id"])
            val.update(changed_vals["value"])
            if end_date:
                val["method_end"] = end_date
            asset = self.create(val)
            if asset.category_id.open_asset:
                if asset.date_first_depreciation == "last_day_period":
                    asset.method_end = end_date
                asset.validate()

    @api.model
    def _cron_generate_journal_entries(self):
        self.compute_generated_journal_entries(datetime.today())

    @api.model
    def compute_generated_journal_entries(
        self, depreciation_date: date, asset_type=None
    ):
        type_domain = []
        if asset_type:
            type_domain.append(("type", "=", asset_type))

        self.asset_ungroup_depreciation(depreciation_date, type_domain)
        self.asset_group_depreciation(depreciation_date, type_domain)

    def asset_ungroup_depreciation(self, depreciation_date: date, type_domain: List):
        domain = type_domain + [
            ("state", "=", "open"),
            ("category_id.group_entries", "=", False),
        ]
        ungrouped_assets = self.env["account.asset.asset"].search(domain)
        ungrouped_assets._compute_journal_entries(depreciation_date)

    def asset_group_depreciation(self, depreciation_date: date, type_domain: List):
        category_domain = type_domain + [("group_entries", "=", True)]
        domain = type_domain + [("state", "=", "open")]
        for grouped_category in self.env["account.asset.category"].search(
            category_domain
        ):
            assets = self.env["account.asset.asset"].search(
                domain + [("category_id", "=", grouped_category.id)]
            )
            assets._compute_journal_entries(depreciation_date, group_entries=True)

    def _compute_journal_entries(self, depreciation_date: date, group_entries=False):
        domain = [
            ("asset_id", "in", self.ids),
            ("depreciation_date", "<=", depreciation_date),
            ("move_check", "=", False),
        ]
        depreciation_ids = self.env["account.asset.depreciation.line"].search(domain)
        monthly_depreciation = self.get_product_depreciation(depreciation_ids)

        if group_entries:
            depreciation_ids.create_grouped_move()
        else:
            depreciation_ids.create_move()

        self.update_depreciation_product_price(monthly_depreciation)

    def get_product_depreciation(self, depreciation_ids: List) -> Dict:
        monthly_depreciation = defaultdict(dict)
        for month, depreciations in groupby(
            sorted(
                filter(lambda d: d.asset_id.product_id, depreciation_ids),
                key=lambda s: s.depreciation_date,
            ),
            key=lambda d: d.depreciation_date,
        ):
            _logger.info(f"month {month}")
            product_depreciation = defaultdict(float)
            for product, lines in groupby(
                sorted(depreciations, key=lambda s: s.asset_id.product_id),
                key=lambda x: x.asset_id.product_id,
            ):
                _logger.info(f"product {product.name}")
                for line in lines:
                    product_depreciation[product] += line.amount

            monthly_depreciation[month] = product_depreciation

        return monthly_depreciation

    def update_product_price(self, product: models.Model, price: float):
        self.env["product.value"].sudo().create(
            ProductValue(
                product_id=product.id,
                value=price,
                company_id=product.company_id.id or self.env.company.id,
                date=fields.Datetime.now(),
                description=_(
                    "Depreciation price update from %(old_price)s to %(new_price)s by %(user)s",
                    old_price=product.standard_price,
                    new_price=price,
                    user=self.env.user.name,
                ),
            ).__dict__
        )

    def update_depreciation_product_price(self, monthly_depreciation: Dict):
        for month, product_depreciation in monthly_depreciation.items():
            _logger.info(f"month {month}")
            products = []
            for product, value in product_depreciation.items():
                if abs(value) <= 0:
                    continue

                quantity = (
                    product._with_valuation_context()
                    .with_context(to_date=month)
                    .qty_available
                )

                price = product.standard_price - (value / quantity or 1)
                _logger.info(f"Product {product.name} price {price}")

                self.update_product_price(product, price)
                products.append(product.id)
                _logger.info("Updated product price for depreciation.")

            # Recompute the standard price
            self.env["product.product"].browse(products)._update_standard_price()
