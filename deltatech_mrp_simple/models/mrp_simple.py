import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class MRPSimple(models.Model):
    _name = "mrp.simple"
    _description = "MRP Simple"

    name = fields.Char()
    consume_id = fields.Many2one("stock.picking", string="Consume", copy=False)
    receipt_id = fields.Many2one("stock.picking", string="Receipt", copy=False)
    state = fields.Selection([("draft", "Draft"), ("done", "Done")], default="draft")
    product_in_ids = fields.One2many(
        "mrp.simple.line.in", "mrp_simple_id", string="Received products", copy=True
    )
    product_out_ids = fields.One2many(
        "mrp.simple.line.out", "mrp_simple_id", string="Consumed products", copy=True
    )

    picking_type_consume = fields.Many2one(
        "stock.picking.type",
        string="Picking type consume",
        required=True,
        domain=[("code", "=", "outgoing")],
    )
    picking_type_receipt_production = fields.Many2one(
        "stock.picking.type", string="Picking type receipt", required=True
    )
    location_src_id = fields.Many2one(
        "stock.location", string="Source Location", domain=[("usage", "=", "internal")]
    )
    location_dest_id = fields.Many2one(
        "stock.location",
        string="Destination Location",
        domain=[("usage", "=", "internal")],
    )

    date = fields.Date(string="Date", default=fields.Date.today, required=True)

    validation_consume = fields.Boolean()
    validation_receipt = fields.Boolean(default=True)

    @api.onchange("picking_type_consume")
    def onchange_location(self):
        self.location_src_id = self.picking_type_consume.default_location_src_id

    @api.onchange("picking_type_receipt_production")
    def onchange_location_dest(self):
        self.location_dest_id = (
            self.picking_type_receipt_production.default_location_dest_id
        )

    def do_transfer(self):
        self.compute_finit_price()
        picking_type_consume = self.picking_type_consume
        picking_type_receipt_production = self.picking_type_receipt_production

        context = {"default_picking_type_id": picking_type_receipt_production.id}
        picking_in = (
            self.env["stock.picking"]
            .with_context(**context)
            .create(
                {
                    "picking_type_id": picking_type_receipt_production.id,
                    "location_dest_id": self.location_dest_id.id,
                    "date_done": self.date,
                }
            )
        )

        context = {"default_picking_type_id": picking_type_consume.id}
        picking_out = (
            self.env["stock.picking"]
            .with_context(**context)
            .create(
                {
                    "picking_type_id": picking_type_consume.id,
                    "location_id": self.location_src_id.id,
                    "date_done": self.date,
                }
            )
        )

        self.create_picking_lines_in(picking_in)
        self.create_picking_lines_out(picking_out)

        self.consume_id = picking_out
        self.receipt_id = picking_in

        # se face consumul
        if picking_out.move_ids:
            picking_out.action_assign()
            if self.validation_consume:
                if picking_out.state == "assigned":
                    for move in picking_out.move_ids:
                        for move_line in move.move_line_ids:
                            move_line.quantity = move_line.quantity_product_uom
                picking_out.button_validate()

        # se face receptia
        if picking_in.move_ids:
            picking_in.action_assign()
            if self.validation_receipt:
                if picking_in.state == "assigned":
                    for move in picking_in.move_ids:
                        for move_line in move.move_line_ids:
                            move_line.quantity = move_line.quantity_product_uom
                            for line in self.product_in_ids:
                                if line.product_id.id == move.product_id.id:
                                    move_line.lot_name = line.lot_name
                picking_in.button_validate()

        self.write({"state": "done"})
        return self

    def add_picking_line(self, picking, line, location_id, location_dest_id):
        move = self.env["stock.move"].search(
            [
                ("picking_id", "=", picking.id),
                ("product_id", "=", line.product_id.id),
                ("product_uom", "=", line.uom_id.id),
            ]
        )
        if move:
            qty = move.product_uom_qty + line.quantity
            move.write({"product_uom_qty": qty})
        else:
            values = {
                "state": "confirmed",
                "product_id": line.product_id.id,
                "product_uom": line.uom_id.id,
                "product_uom_qty": line.quantity,
                # 'quantity_done': quantity,  # o fi bine >???
                "picking_id": picking.id,
                "price_unit": line.price_unit,
                "location_id": location_id,
                "location_dest_id": location_dest_id,
                "picking_type_id": picking.picking_type_id.id,
                "simple_mrp_id": self.id,
            }

            move = self.env["stock.move"].create(values)
        return move

    def open_consume(self):
        self.ensure_one()
        return {
            "res_id": self.consume_id.id,
            "target": "current",
            "name": self.env._("Consume"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.picking",
            "view_id": self.env.ref("stock.view_picking_form").id,
            "context": {},
            "type": "ir.actions.act_window",
        }

    def open_receipt(self):
        self.ensure_one()
        return {
            "res_id": self.receipt_id.id,
            "target": "current",
            "name": self.env._("Receipt"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.picking",
            "view_id": self.env.ref("stock.view_picking_form").id,
            "context": {},
            "type": "ir.actions.act_window",
        }

    def compute_finit_price(self):
        self.ensure_one()
        if not len(self.product_out_ids) == len(self.product_in_ids):
            raise UserError(_("Product doesn't match!"))

        for line_out, line_in in zip(self.product_out_ids, self.product_in_ids):
            line_in.price_unit = line_out.value / line_in.quantity

    def create_picking_lines_in(self, picking_in):
        if not self.product_in_ids:
            raise UserError(self.env._("You need at least one final product"))

        location_id = picking_in.picking_type_id.default_location_src_id.id
        location_dest_id = picking_in.location_dest_id.id
        for line in self.product_in_ids:
            params = self.env["ir.config_parameter"].sudo()
            allow_zero = safe_eval(
                params.get_param("deltatech_mrp_simple.allow_zero_cost", False)
            )
            if not line.price_unit and not allow_zero:
                raise UserError(self.env._("Price 0 for result product!"))

            if line.product_id.type != "service":
                self.add_picking_line(
                    picking=picking_in,
                    line=line,
                    location_id=location_id,
                    location_dest_id=location_dest_id,
                )

    def create_picking_lines_out(self, picking_out):
        location_id = picking_out.location_id.id
        location_dest_id = picking_out.picking_type_id.default_location_dest_id.id
        for line in self.product_out_ids:
            if line.product_id.type != "service":
                self.add_picking_line(
                    picking=picking_out,
                    line=line,
                    location_id=location_id,
                    location_dest_id=location_dest_id,
                )

    def add_multiple_lines(self):
        self.ensure_one()
        view = self.env.ref("deltatech_mrp_simple.multi_add_view_form")
        wiz = self.env["add.multi.mrp.lines"].create({"simple_mrp_id": self.id})
        return {
            "name": self.env._("Add lines"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "add.multi.mrp.lines",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": wiz.id,
            "context": self.env.context,
        }


class MRPSimpleLineIn(models.Model):
    _name = "mrp.simple.line.in"
    _description = "MRP Simple Line IN"

    mrp_simple_id = fields.Many2one("mrp.simple")
    product_id = fields.Many2one("product.product")
    quantity = fields.Float(
        string="Quantity", digits="Product Unit of Measure", default=1
    )
    price_unit = fields.Float("Unit Price", digits="Product Price")
    uom_id = fields.Many2one("uom.uom", "Unit of Measure")
    value = fields.Float(compute="_compute_value", string="Value", store=True)
    lot_name = fields.Char("Lot/Serial Number Name")

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.uom_id = self.product_id.uom_id

    @api.onchange("quantity")
    def compute_finit_price(self):
        mrpsimple = self.mrp_simple_id
        for line_out, line_in in zip(
            mrpsimple.product_out_ids, mrpsimple.product_in_ids
        ):
            line_in.price_unit = line_out.value / line_in.quantity

    @api.depends("quantity", "price_unit")
    def _compute_value(self):
        for line in self:
            line.value = line.quantity * line.price_unit


class MRPSimpleLineOut(models.Model):
    _name = "mrp.simple.line.out"
    _description = "MRP Simple Line OUT"

    mrp_simple_id = fields.Many2one("mrp.simple")
    product_id = fields.Many2one("product.product")
    quantity = fields.Float(
        string="Quantity", digits="Product Unit of Measure", default=1
    )
    price_unit = fields.Float("Unit Price", digits="Product Price")
    uom_id = fields.Many2one("uom.uom", "Unit of Measure")
    stock = fields.Float(related="product_id.qty_available")
    location_qty = fields.Float(
        compute="_compute_location_quantity", string="Location Qty"
    )
    value = fields.Float(compute="_compute_value", string="Value", store=True)

    @api.depends("quantity", "price_unit")
    def _compute_value(self):
        for line in self:
            line.value = line.quantity * line.price_unit

    @api.depends("mrp_simple_id.location_src_id")
    def _compute_location_quantity(self):
        location_id = self.mrp_simple_id.location_src_id.id
        for line in self:
            stock_quant = self.env["stock.quant"].search(
                [
                    ("product_id", "=", line.product_id.id),
                    ("location_id", "=", location_id),
                ]
            )
            line.location_qty = sum(stock_quant.mapped("quantity"))

    @api.onchange("product_id", "quantity")
    def onchange_product_id(self):
        self.uom_id = self.product_id.uom_id
        self.price_unit = self.product_id.standard_price
