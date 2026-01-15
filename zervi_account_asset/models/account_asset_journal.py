# pylint: disable = (protected-access)
import json
import logging
from collections import defaultdict
from datetime import date, datetime
from itertools import groupby
from typing import Dict, List

from odoo import _, api, fields, models
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

    def _build_query(self, depreciation_date: str, group_entries: bool) -> str:
        query = Query.get_depreciations.format(
            company_id=self.env.company.id,
            group_entries=group_entries,
            status=LineStatus.DRAFT.code,
            depreciation_date=depreciation_date,
        )
        _logger.info("#===== query %s ", query)
        return query

    def get_asset_depreciation(
        self, depreciation_date: str, group_entries: bool = False
    ):
        self.env.cr.execute(
            self._build_query(
                depreciation_date=depreciation_date, group_entries=group_entries
            )
        )
        return self.env.cr.fetchall()

    def update_depreciation_line(self, status: str, line_ids: list):
        self.env.cr.execute(Query.updaate_depreciation, (status, tuple(line_ids)))

    @staticmethod
    def get_derpreciation_ids(depreciation_data):
        return [data[DepreCols.DEP_IDS] for data in depreciation_data]

    @api.model
    def _cron_generate_journal_entries(self):
        self.compute_generated_journal_entries(datetime.today())

    @api.model
    def compute_generated_journal_entries(
        self, depreciation_date: date, asset_type: str = None
    ):
        self.asset_ungroup_depreciation(depreciation_date, asset_type)
        self.asset_group_depreciation(depreciation_date, asset_type)

    def asset_ungroup_depreciation(
        self, depreciation_date: date, asset_type: str = None
    ):
        asset_depreciations = self.get_asset_depreciation(
            depreciation_date=depreciation_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        )
        self._compute_journal_entries(asset_depreciations)

    def asset_group_depreciation(self, depreciation_date: date, asset_type: str = None):
        asset_depreciations = self.get_asset_depreciation(
            depreciation_date=depreciation_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
            group_entries=True,
        )
        for category, depreciations in groupby(
            sorted(asset_depreciations, key=lambda x: x[DepreCols.CATEGORY_ID]),
            key=lambda x: x[DepreCols.CATEGORY_ID],
        ):
            _logger.info("# Asset Category ID : %s ", category)
            self._compute_journal_entries(list(depreciations), group_entries=True)

    def _compute_journal_entries(
        self, asset_depreciations: list, group_entries: bool = False
    ):
        _logger.info("#====== compute journal entries : %s", asset_depreciations)
        asset_line = self.env["account.asset.depreciation.line"]
        for month, depreciation in groupby(
            sorted(asset_depreciations, key=lambda d: d[DepreCols.MONTH]),
            lambda d: d[DepreCols.MONTH],
        ):
            depreciation = list(depreciation)
            _logger.info(
                "# ===========  Asset depreciation moht : %s , depreciation : %s",
                month,
                depreciation,
            )
            depreciation_ids = self.get_derpreciation_ids(depreciation)
            _logger.info("Depreciaiotn ids %s ", depreciation_ids)
            if depreciation_ids:
                self.update_depreciation_product_cost(depreciation)
                if group_entries:
                    asset_line.browse(depreciation_ids).create_grouped_move()
                    # self.with_delay_entries(
                    #     month=month,
                    #     depreciation_ids=depreciation_ids,
                    #     method="create_grouped_move",
                    # )
                else:
                    asset_line.browse(depreciation_ids).create_move()
                    # self.with_delay_entries(
                    #     month=month,
                    #     depreciation_ids=depreciation_ids,
                    #     method="create_move",
                    # )

        # we re-evaluate the assets to determine if we can close them
        for asset in self:
            if asset.currency_id.is_zero(asset.value_residual):
                asset.state = State.CLOSE.code

    def create_product_depreciation_cost(
        self, product_id: int, value: float, move_id: int = None, lot_id: int = None
    ):
        self.env["product.value"].sudo().create(
            ProductValue(
                product_id=product_id,
                value=value,
                date=fields.Datetime.now(),
                description=_(
                    "Depreciation price updated %(new_price)s by %(user)s",
                    new_price=value,
                    user=self.env.user.name,
                ),
                lot_id=lot_id,
                move_id=move_id,
                company_id=self.env.company.id,
            ).__dict__
        )

    def update_depreciation_product_cost(self, depreciations: List):
        for product_method, product_dep in groupby(
            depreciations,
            key=lambda x: (x[DepreCols.PRODUCT], x[DepreCols.COST_METHOD]),
        ):
            products = []
            if product_method[1] == "fifo":
                for dep in product_dep:
                    self.create_product_depreciation_cost(
                        product_id=dep[DepreCols.PRODUCT],
                        value=dep[DepreCols.COST],
                        lot_id=dep[DepreCols.LOT_ID],
                        move_id=dep[DepreCols.MOVE_ID],
                    )
                products.append(product_method[0])
                _logger.info("Updated product fifo price for depreciation.")
            if product_method[1] == "average":
                value = 0.0
                month = ""
                for dep in product_dep:
                    _logger.info("#Average dpe %s", dep)
                    value += dep[DepreCols.AMOUNT]
                    month = dep[DepreCols.MONTH]

                if not value:
                    continue
                product = self.env["product.product"].browse(product_method[0])
                _logger.info("# Month %s ", month)
                quantity = (
                    product._with_valuation_context()
                    .with_context(to_date=month)
                    .qty_available
                )
                if quantity:
                    price = product.standard_price - (value / (quantity or 1))
                    _logger.info(f"Product {product.name} price {price}")

                    self.create_product_depreciation_cost(
                        product_id=product.id, value=price
                    )
                    products.append(product.id)
                    _logger.info("Updated product price for depreciation.")

            # Recompute the standard price
            self.env["product.product"].browse(products)._update_standard_price()

    @staticmethod
    def split_by_batch(lst, batch_size):
        for i in range(0, len(lst), batch_size):
            yield lst[i : i + batch_size]

    def with_delay_entries(
        self,
        month: date,
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
                    description=f"Asset {month} {method} : {len(depreciation)}",
                ).entries(assets=json.dumps(depreciation), method=method)

    def entries(self, assets: str, method: str):
        _logger.info("# depreciation ids %s", assets)
        with Registry(self.env.cr.dbname).cursor() as new_cr:
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            depreciations = new_env["account.asset.depreciation.line"].browse(
                json.loads(assets)
            )
            # if method == "create_grouped_move":
            #     moves = depreciations.create_grouped_move()
            # else:
            #     moves = depreciations.create_move()
            moves = getattr(depreciations, method, None)
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
