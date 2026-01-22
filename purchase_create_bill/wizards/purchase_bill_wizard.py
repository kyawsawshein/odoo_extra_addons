from odoo import _, api, fields, models


class PurchaseCreateBillWizard(models.TransientModel):
    _name = "purchase.create.bill.wizard"
    _description = "Purchase Create Bill Wizard"

    purchase_order_id = fields.Many2one(
        "purchase.order", string="Purchase Order", required=True
    )
    bill_option = fields.Selection(
        [
            ("ready_only", "Create bill for ready items only"),
            ("wait_all", "Wait for all items to be ready"),
        ],
        string="Billing Option",
        default="ready_only",
        required=True,
    )

    ready_lines = fields.Text(string="Ready to Bill", readonly=True)
    waiting_lines = fields.Text(string="Waiting to be Received", readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_model") == "purchase.order":
            purchase_id = self.env.context.get("active_id")
            if purchase_id:
                purchase_order = self.env["purchase.order"].browse(purchase_id)
                res["purchase_order_id"] = purchase_id

                # Analyze lines
                ready_lines = []
                waiting_lines = []

                for line in purchase_order.order_line:
                    if line.product_qty <= 0 or not line.product_id:
                        continue

                    if line.product_id.purchase_method == "purchase":
                        # Can bill immediately
                        qty_to_bill = line.product_qty - line.qty_invoiced
                        if qty_to_bill > 0:
                            ready_lines.append(
                                f"• {line.product_id.name} - Qty: {qty_to_bill} (Can immediately billed)"
                            )
                    elif line.product_id.purchase_method == "receive":
                        # Need to receive first
                        qty_received = line.qty_received
                        qty_ordered = line.product_qty
                        qty_invoiced = line.qty_invoiced

                        # Check if there's quantity ready to bill (already received)
                        qty_ready_to_bill = qty_received - qty_invoiced
                        if qty_ready_to_bill > 0:
                            ready_lines.append(
                                f"• {line.product_id.name} - Qty: {qty_ready_to_bill} (Already received)"
                            )

                        # Check if there's quantity still waiting to be received
                        qty_waiting = qty_ordered - qty_received
                        if qty_waiting > 0:
                            waiting_lines.append(
                                f"• {line.product_id.name} - Qty: {qty_waiting} (Need to receive)"
                            )

                res["ready_lines"] = (
                    "\n".join(ready_lines) if ready_lines else "No items ready to bill"
                )
                res["waiting_lines"] = (
                    "\n".join(waiting_lines) if waiting_lines else "No items waiting"
                )

        return res

    def action_create_bill(self):
        """Create bill based on selected option"""
        if self.bill_option == "wait_all":
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "message": _(
                        "Please receive all pending items first, then try creating the bill again."
                    ),
                    "type": "warning",
                    "sticky": False,
                },
            }

        # pylint: disable=W0212
        # Create bill for ready items only
        return self.purchase_order_id._create_vendor_bill_internal(ready_only=True)

    def action_cancel(self):
        """Cancel wizard"""
        return {"type": "ir.actions.act_window_close"}
