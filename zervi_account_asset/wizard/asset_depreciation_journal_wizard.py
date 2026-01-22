from odoo import fields, models


class AssetDepreciationConfirmationWizard(models.TransientModel):
    _name = "asset.depreciation.confirmation.wizard"
    _description = "asset.depreciation.confirmation.wizard"

    date = fields.Date(
        "Account Date",
        required=True,
        help="Choose the period for which you want to automatically"
        "post the depreciation lines of running assets",
        default=fields.Date.context_today,
    )

    def asset_journal_compute(self):
        self.ensure_one()
        context = self.env.context
        self.env["account.asset.asset"].compute_generated_journal_entries(
            self.date, asset_type=context.get("asset_type")
        )
        return {"type": "ir.actions.act_window_close"}
