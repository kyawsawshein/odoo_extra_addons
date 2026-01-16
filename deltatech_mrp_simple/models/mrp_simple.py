import logging
from typing import List

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ...data_commom.datamodels.datamodel import LineData, MoveData, PickingData

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
        "stock.picking.type",
        string="Picking type receipt",
        required=True,
        domain=[("code", "=", "incoming")],
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

    def add_move_out_line(
        self,
        line,
        location_id: int,
        location_dest_id: int,
        qty: float,
        lot_id: int = None,
    ):
        return LineData(
            product_id=line.product_id.id,
            product_uom_id=line.product_id.uom_id.id,
            location_id=location_id,
            location_dest_id=location_dest_id,
            lot_id=lot_id,
            quantity=qty,
        ).__dict__

    def add_move_in_line(
        self,
        line,
        location_id: int,
        location_dest_id: int,
        qty: float,
        lot_name: str = "",
    ):
        return LineData(
            product_id=line.product_id.id,
            product_uom_id=line.product_id.uom_id.id,
            location_id=location_id,
            location_dest_id=location_dest_id,
            lot_name=lot_name,
            quantity=qty,
        ).__dict__

    def _prepare_move_out(self, lines, location_id, location_dest_id) -> List:
        moves = []
        for line in lines:
            move = MoveData(
                location_id=location_id,
                location_dest_id=location_dest_id,
                product_id=line.product_id.id,
                product_uom=line.uom_id.id,
                product_uom_qty=line.quantity,
                price_unit=line.price_unit,
                simple_mrp_id=line.mrp_simple_id.id,
            )
            move_lines = []
            quantity = line.quantity
            if line.lot_ids:
                for lot in line.lot_ids:
                    qty = min(lot.product_qty, quantity)
                    move_lines.append(
                        (
                            0,
                            0,
                            self.add_move_out_line(
                                line,
                                location_id,
                                location_dest_id,
                                qty=qty,
                                lot_id=lot.id,
                            ),
                        )
                    )
                    quantity -= qty
                    if quantity <= 0:
                        break
            else:
                move_lines.append(
                    (
                        0,
                        0,
                        self.add_move_out_line(
                            line, location_id, location_dest_id, qty=quantity
                        ),
                    )
                )
            move.move_line_ids = move_lines
            moves.append((0, 0, move.__dict__))
        return moves

    def _prepare_move_in(self, lines, location_id, location_dest_id) -> List:
        moves = []
        for line in lines:
            move = MoveData(
                picking_type_id=self.picking_type_receipt_production.id,
                location_id=location_id,
                location_dest_id=location_dest_id,
                product_id=line.product_id.id,
                product_uom=line.uom_id.id,
                product_uom_qty=line.quantity,
                price_unit=line.price_unit,
                simple_mrp_id=line.mrp_simple_id.id,
                move_line_ids=[
                    (
                        0,
                        0,
                        self.add_move_in_line(
                            line,
                            location_id,
                            location_dest_id,
                            qty=line.quantity,
                            lot_name=line.lot_name,
                        ),
                    )
                ],
            )
            moves.append((0, 0, move.__dict__))
        return moves

    def prepare_picking(
        self, picking_type_id: int, location_id: int, location_dest_id: int
    ):
        picking = PickingData(
            picking_type_id=picking_type_id,
            location_id=location_id,
            location_dest_id=location_dest_id,
            date_done=fields.Datetime.now(),
        )
        return picking

    def create_picking_lines_out(self, context):
        picking_type = self.picking_type_consume
        location_id = self.location_src_id.id
        location_dest_id = picking_type.default_location_dest_id.id

        picking_data = self.prepare_picking(
            picking_type_id=picking_type.id,
            location_id=location_id,
            location_dest_id=location_dest_id,
        )
        picking_data.move_ids = self._prepare_move_out(
            lines=self.product_out_ids,
            location_id=location_id,
            location_dest_id=location_dest_id,
        )
        _logger.info("# ===== Picking Data Out : %s ", picking_data)
        return (
            self.env["stock.picking"]
            .with_context(**context)
            .create(picking_data.__dict__)
        )

    def create_picking_lines_in(self, context):
        picking_type = self.picking_type_receipt_production
        location_id = picking_type.default_location_src_id.id
        location_dest_id = self.location_dest_id.id
        picking_data = self.prepare_picking(
            picking_type_id=picking_type.id,
            location_id=location_id,
            location_dest_id=location_dest_id,
        )
        picking_data.move_ids = self._prepare_move_in(
            lines=self.product_in_ids,
            location_id=location_id,
            location_dest_id=location_dest_id,
        )
        _logger.info("# ===== Picking Data In : %s ", picking_data)
        return (
            self.env["stock.picking"]
            .with_context(**context)
            .create(picking_data.__dict__)
        )

    def do_transfer(self):
        self.compute_finit_price()
        picking_type_consume = self.picking_type_consume
        picking_type_receipt_production = self.picking_type_receipt_production

        context_out = {"default_picking_type_id": picking_type_consume.id}
        context_in = {"default_picking_type_id": picking_type_receipt_production.id}
        picking_out = self.create_picking_lines_out(context_out)
        picking_in = self.create_picking_lines_in(context_in)
        self.consume_id = picking_out
        self.receipt_id = picking_in

        # se face consumul
        if picking_out.move_ids:
            picking_out.action_assign()
            _logger.info("# Out picking state %s ", picking_out.state)
            if self.validation_consume and picking_out.state == "assigned":
                picking_out.button_validate()
        _logger.info("Done validaet picking for out.")

        # se face receptia
        if picking_in.move_ids:
            picking_in.action_assign()
            if self.validation_receipt and picking_in.state == "assigned":
                picking_in.button_validate()
        _logger.info("Done validaet picking for in.")

        self.write({"state": "done"})
        return self

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


class MRPSimpleLineIn(models.Model):
    _name = "mrp.simple.line.in"
    _description = "MRP Simple Line IN"

    mrp_simple_id = fields.Many2one("mrp.simple")
    product_id = fields.Many2one(
        "product.product",
        domain="[('default_code', 'in', raw_product_domain)] if raw_product_domain else []",
    )
    quantity = fields.Float(
        string="Quantity", digits="Product Unit of Measure", default=1
    )
    price_unit = fields.Float("Unit Price", digits="Product Price")
    uom_id = fields.Many2one("uom.uom", "Unit of Measure")
    value = fields.Float(compute="_compute_value", string="Value", store=True)
    lot_name = fields.Char("Lot/Serial Number Name")

    raw_product_domain = fields.Json(compute="_compute_raw_product_domain")
    expired_date = fields.Date()

    def _compute_raw_product_domain(self):
        self.raw_product_domain = []

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
    price_unit = fields.Float("Price", digits="Product Price")
    uom_id = fields.Many2one("uom.uom", "Unit")
    stock = fields.Float(related="product_id.qty_available", string="Onhand")

    value = fields.Float(compute="_compute_value", string="Value", store=True)
    lot_ids = fields.Many2many(
        comodel_name="stock.lot", string="Lot", domain="[('id', 'in', lot_domain)]"
    )
    lot_domain = fields.Json(compute="_compute_lot_domain")
    lot_qty = fields.Float(compute="_compute_location_quantity", string="Lot Qty")

    @api.depends("quantity", "price_unit")
    def _compute_value(self):
        for line in self:
            line.value = line.quantity * line.price_unit

    def _get_location_quant(self, product_id: int, location_id: int):
        return self.env["stock.quant"].search(
            [
                ("product_id", "=", product_id),
                ("location_id", "=", location_id),
            ]
        )

    @api.depends("mrp_simple_id.location_src_id")
    def _compute_lot_domain(self):
        location_id = self.mrp_simple_id.location_src_id.id
        for line in self:
            stock_quant = self._get_location_quant(line.product_id.id, location_id)
            line.lot_domain = stock_quant.mapped("lot_id").ids

    @api.depends("lot_ids")
    def _compute_location_quantity(self):
        location_id = self.mrp_simple_id.location_src_id.id
        for line in self:
            if line.lot_ids:
                line.lot_qty = sum(line.lot_ids.mapped("product_qty"))
            else:
                line.lot_qty = sum(
                    self._get_location_quant(line.product_id.id, location_id).mapped(
                        "quantity"
                    )
                )

    @api.onchange("product_id", "quantity")
    def onchange_product_id(self):
        self.uom_id = self.product_id.uom_id
        self.price_unit = self.product_id.standard_price
