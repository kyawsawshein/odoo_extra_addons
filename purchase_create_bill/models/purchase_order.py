from odoo import  models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_create_vendor_bill(self):
        """Create a vendor bill based on the purchase order."""
        # Check if the purchase order is confirmed
        if self.state not in ["purchase", "done"]:
            raise UserError(
                _("You can only create bills for confirmed purchase orders.")
            )

        # Check if partner is set
        if not self.partner_id:
            raise UserError(_("You must set a vendor before creating a bill."))

        # Analyze purchase methods in order lines
        purchase_method_lines = []  # Can bill immediately
        receive_method_lines = []  # Need to receive first
        mixed_scenario = False

        for line in self.order_line:
            if not line.product_id or line.product_qty <= 0:
                continue

            if line.product_id.purchase_method == "purchase":
                # Can bill immediately
                qty_to_bill = line.product_qty - line.qty_invoiced
                if qty_to_bill > 0:
                    purchase_method_lines.append(line)
            elif line.product_id.purchase_method == "receive":
                # Need to receive first
                qty_received = line.qty_received
                qty_to_bill = qty_received - line.qty_invoiced
                if qty_to_bill > 0:
                    receive_method_lines.append(line)
                elif qty_received < line.product_qty:
                    # Has items not yet received
                    mixed_scenario = True

        # Check if we have mixed scenario
        ready_lines = purchase_method_lines + receive_method_lines

        if not ready_lines and not mixed_scenario:
            raise UserError(
                _(
                    "There are no products to bill. Please receive products first or check your purchase order lines."
                )
            )

        # If mixed scenario, show wizard
        if mixed_scenario and ready_lines:
            return {
                "name": _("Create Vendor Bill"),
                "type": "ir.actions.act_window",
                "res_model": "purchase.create.bill.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "active_model": "purchase.order",
                    "active_id": self.id,
                },
            }

        # If all ready, create bill directly
        return self._create_vendor_bill_internal()

    def _create_vendor_bill_internal(self):
        """Internal method to create vendor bill"""
        # Prepare invoice values
        invoice_vals = {
            "move_type": "in_invoice",
            "partner_id": self.partner_id.id,
            "currency_id": self.currency_id.id,
            "payment_reference": self.partner_ref or self.name,
            "invoice_origin": self.name,
            "ref": self.partner_ref or self.name,
            "company_id": self.company_id.id,
        }

        # Prepare invoice line values with new logic
        invoice_lines = []
        for line in self.order_line:
            if not line.product_id or line.product_qty <= 0:
                continue

            qty_to_bill = 0

            if line.product_id.purchase_method == "purchase":
                # Can bill immediately - use ordered quantity
                qty_to_bill = line.product_qty - line.qty_invoiced
            elif line.product_id.purchase_method == "receive":
                # Need to receive first - use received quantity
                qty_received = line.qty_received
                qty_to_bill = qty_received - line.qty_invoiced

            # Skip if no quantity to bill
            if qty_to_bill <= 0:
                continue

            # Prepare line values
            line_vals = {
                "product_id": line.product_id.id,
                "name": line.name,
                "quantity": qty_to_bill,
                "product_uom_id": line.product_uom_id.id,
                "price_unit": line.price_unit,
                "tax_ids": [(6, 0, line.tax_ids.ids)],
                "analytic_distribution": line.analytic_distribution,
                "purchase_line_id": line.id,
            }
            invoice_lines.append((0, 0, line_vals))

        if not invoice_lines:
            raise UserError(
                _("There are no products to bill. Please receive products first.")
            )

        invoice_vals["invoice_line_ids"] = invoice_lines

        # Create the vendor bill
        invoice = self.env["account.move"].create(invoice_vals)

        # Return action to open the created bill
        action = {
            "name": _("Vendor Bill"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": invoice.id,
            "target": "current",
            "context": dict(self.env.context),
        }

        return action
