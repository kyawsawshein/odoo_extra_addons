# pylint: disable = (protected-access)
import calendar
import json
import logging
from collections import defaultdict
from datetime import date, datetime
from itertools import groupby
from typing import Dict, List

from odoo import _, api, fields, models
from odoo.fields import Domain
from odoo.modules.registry import Registry
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

from ..datamodels.asset_data import LineStatus, State
from ..datamodels.product_data import ProductValue
from ..helper.query import DepreCols, Query

_logger = logging.getLogger(__name__)

ASSET_BATCH = 100


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Float(string="Quantity")
    lot_name = fields.Char(string="Lot Name")

    def create_asset(self, vals: List[Dict], end_date: str = None):
        for val in vals:
            changed_vals = self.onchange_category_id_values(val["category_id"])
            val.update(changed_vals["value"])
            if end_date:
                val["method_end"] = end_date
            asset = self.create(val)
            if asset.category_id.open_asset:
                if asset.date_first_depreciation == "last_day_period" and end_date:
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
            ("state", "=", State.OPEN.code),
            ("category_id.group_entries", "=", False),
        ]
        ungrouped_assets = self.env["account.asset.asset"].search(domain)
        if ungrouped_assets:
            ungrouped_assets._compute_journal_entries(depreciation_date)

    def asset_group_depreciation(self, depreciation_date: date, type_domain: List):
        category_domain = type_domain + [("group_entries", "=", True)]
        domain = type_domain + [("state", "=", State.OPEN.code)]
        for grouped_category in self.env["account.asset.category"].search(
            category_domain
        ):
            assets = self.env["account.asset.asset"].search(
                domain + [("category_id", "=", grouped_category.id)]
            )
            if assets:
                assets._compute_journal_entries(depreciation_date, group_entries=True)

    def _compute_journal_entries(self, depreciation_date: date, group_entries=False):
        domain = [
            ("asset_id", "in", self.ids),
            ("depreciation_date", "<=", depreciation_date),
            ("move_check", "=", False),
            ("status", "=", LineStatus.DRAFT.code),
        ]
        depreciations = self.env["account.asset.depreciation.line"].search(domain)
        if not depreciations:
            return

        monthly_depreciation = self.get_product_depreciation(depreciations)
        self.update_depreciation_line(
            status=LineStatus.PROGRESS.code, line_ids=depreciations.ids
        )

        if group_entries:
            # depreciation_ids.create_grouped_move()
            self.with_delay_entries(
                date_end=depreciation_date,
                depreciation_ids=depreciations.ids,
                method="create_grouped_move",
            )
        else:
            # depreciation_ids.create_move()
            self.with_delay_entries(
                date_end=depreciation_date,
                depreciation_ids=depreciations.ids,
                method="create_move",
            )

        # we re-evaluate the assets to determine if we can close them
        for asset in self:
            if asset.currency_id.is_zero(asset.value_residual):
                asset.state = State.CLOSE.code

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

                price = product.standard_price - (value / (quantity or 1))
                _logger.info(f"Product {product.name} price {price}")

                self.update_product_price(product, price)
                products.append(product.id)
                _logger.info("Updated product price for depreciation.")

            # Recompute the standard price
            self.env["product.product"].browse(products)._update_standard_price()

    def update_depreciation_line(self, status: str, line_ids: list):
        self.env.cr.execute(Query.updaate_depreciation, (status, tuple(line_ids)))

    @staticmethod
    def split_by_batch(lst, batch_size):
        for i in range(0, len(lst), batch_size):
            yield lst[i : i + batch_size]

    def with_delay_entries(
        self,
        date_end: date,
        depreciation_ids: List[int],
        method: str,
        channel: str = "root",
    ):
        if depreciation_ids:
            entry_limit = (
                int(
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("asset.entry.batch")
                )
                or ASSET_BATCH
            )
            for depreciation in self.split_by_batch(depreciation_ids, entry_limit):
                _logger.info("Depraciation ..... %s ", depreciation)
                self.with_delay(
                    channel=channel,
                    description=f"Asset {date_end} {method} : {len(depreciation)}",
                ).entries(assets=json.dumps(depreciation), method=method)

    def entries(self, assets: str, method: str):
        with Registry(self.env.cr.dbname).cursor() as new_cr:
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            depreciations = new_env["account.asset.depreciation.line"].browse(
                json.loads(assets)
            )
            if method == "create_grouped_move":
                moves = depreciations.create_grouped_move()
            moves = depreciations.create_move()
            # move = getattr(depreciations, method, None)
            self.update_depreciation_line(
                status=LineStatus.DONE.code, line_ids=depreciations.ids
            )
            _logger.info("# ==================== Done depreciation %s", moves)


class AccountAssetDepreciationLine(models.Model):
    _inherit = "account.asset.depreciation.line"

    status = fields.Selection(
        selection=LineStatus.get_list(),
        string="Status",
        required=True,
        copy=False,
        default="draft",
    )
