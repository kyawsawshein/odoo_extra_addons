"""
Business Operations API Controller
Provides REST API endpoints for Odoo business operations
"""

import json
import logging
from datetime import datetime
from typing import Dict, List

from odoo import http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

from ...data_commom.datamodels.datamodel import (
    LineData,
    MoveData,
    PickingData,
    default_ids,
)

_logger = logging.getLogger(__name__)


from odoo import http
from odoo.http import request

# teable_accT5fdyermOdrlIf1p_Shm3m5U966h4kesCBf0tmr/m2Yyns0Cw4Xc9BwWf+dM=
class ProductAPI(http.Controller):

    def add_move_line(self, value) -> LineData:
        return LineData(
            product_id=value.get("product_id"),
            product_uom_id=value.get("uom_id"),
            location_id=1,
            location_dest_id=5,
            quantity=value.get("quantity"),
            lot_name=value.get("lot_name"),
        )

    def add_move(self, value) -> MoveData:
        return MoveData(
            location_id=1,
            location_dest_id=5,
            product_id=value.get("product_id"),
            product_uom=value.get("uom_id"),
            product_uom_qty=value.get("quantity"),
            price_unit=value.get("price"),
        )

    def _prepare_move_in(self, value) -> Dict:
        moves = []
        move = self.add_move(value)
        move.move_line_ids = [default_ids(self.add_move_line(value))]
        return move.to_dict()

    # def do_receive(self, value: Dict):
    #     move = self._prepare_move_in(value)
    #     # se face receptia
    #     if move:
    #         move._action_assign()
    #         move.action_done()

    #     _logger.info("Done create stock move in.")
    #     return move.name

    @http.route(
        "/api/product/search", type="json", auth="bearer", methods=["POST"], csrf=False
    )
    def product_search(self):
        # Debug logging - very useful right now
        _logger.info(
            "Content-Type: %s", request.httprequest.headers.get("Content-Type")
        )
        _logger.info("Body length: %s", len(request.httprequest.data or b""))
        if request.httprequest.data:
            _logger.info(
                "Raw body preview: %s",
                request.httprequest.data.decode("utf-8", errors="replace")[:400],
            )

        try:
            payload = (
                request.httprequest.json
            )  # ← this is the correct attribute in Odoo 19
            _logger.info("Parsed JSON payload: %s", payload)
        except Exception as e:
            _logger.error("Failed to parse JSON: %s", e)
            return {"error": "Invalid JSON body", "details": str(e)}

        # Now safely access your structure
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})

        domain = kwargs.get("domain", [])
        if not domain and args:
            domain = args[0] if isinstance(args[0], list) else []

        limit = kwargs.get("limit")

        _logger.info("Domain used: %s | Limit: %s", domain, limit)

        products = request.env["product.product"].search(domain, limit=limit)

        return {
            "id": products.id,
            "uom_id": products.uom_id.id,
        }  # or return {"ids": products.ids} if you prefer

    @http.route(
        "/api/stock/receive", type="json", auth="bearer", methods=["POST"], csrf=False
    )
    def stock_receive(self):
        # Debug logging - very useful right now
        _logger.info(
            "Content-Type: %s", request.httprequest.headers.get("Content-Type")
        )
        _logger.info("Body length: %s", len(request.httprequest.data or b""))
        if request.httprequest.data:
            _logger.info(
                "Raw body preview: %s",
                request.httprequest.data.decode("utf-8", errors="replace")[:400],
            )

        try:
            payload = (
                request.httprequest.json
            )  # ← this is the correct attribute in Odoo 19
            _logger.info("Parsed JSON payload: %s", payload)
        except Exception as e:
            _logger.error("Failed to parse JSON: %s", e)
            return {"error": "Invalid JSON body", "details": str(e)}

        # Now safely access your structure
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        _logger.info("Args : %s, Kwargs : %s", args, kwargs)
        move_data = self._prepare_move_in(kwargs)
        _logger.info("stock move data : %s ", move_data)
        move = request.env["stock.move"].sudo().create(move_data)
        move._action_assign()
        move._action_done()
        return move.id


# class BusinessOperationsController(http.Controller):
#     """Controller for business operations API endpoints"""


#     @http.route('/api/product/search', type='json', auth='api_key')
#     def product_search(self, domain):
#         products = request.env['product.product'].search(domain)
#         return products.ids
# @http.route(
#     "/api/product/search", type="json", auth="bearer", methods=["POST"], csrf=False
# )
# def product_search(self, **kwargs):
#     _logger.info("parameter value %s", kwargs)
#     _logger.info("Raw json request: %s", request.httprequest)
#     domain = kwargs.get("domain", [])
#     limit = kwargs.get("limit")

#     products = request.env["product.product"].search(domain, limit=limit)

#     return products.ids

# @http.route("/api/product/search", type="json", auth="public", methods=["POST"], csrf=False)
# def product_search(self, **kwargs):
#     _logger.info("Received kwargs: %s", request.httprequest.data.decode())
#     _logger.info("Headers: %s", dict(request.httprequest.headers))
#     data  = request.httprequest.data.
#     args = data.get("args", [])
#     kwargs = data.get("kwargs", {})
#     domain = args[0] if args else []
#     products = request.env["product.product"].search(
#         domain,
#         **kwargs
#     )
# majzrcivop8.cloudpepper.site
#     return products.ids

#     # Helper methods
#     def _authenticate_api_key(self):
#         """Authenticate using API key from headers"""
#         api_key = request.httprequest.headers.get("X-API-Key")
#         if not api_key:
#             return None

#         # Find API token in database
#         api_token = (
#             request.env["api.token"]
#             .sudo()
#             .search([("token", "=", api_key), ("is_active", "=", True)], limit=1)
#         )

#         if not api_token:
#             return None

#         # Check if token is expired
#         if api_token.expires_at and api_token.expires_at < datetime.now():
#             return None

#         return api_token.user_id

#     def _authenticate_request(self):
#         """Authenticate request using API key or JWT token"""
#         # Check for API key
#         user = self._authenticate_api_key()
#         if user:
#             return user

#         # Check for JWT token
#         auth_header = request.httprequest.headers.get("Authorization")
#         if auth_header and auth_header.startswith("Bearer "):
#             token = auth_header[7:]
#             try:
#                 config = request.env["api.config"].sudo()
#                 payload = config.decode_token(token=token)
#                 return request.env["res.users"].sudo().browse(payload.get("uid"))
#             except Exception:
#                 pass

#         return None

#     def _create_response(
#         self, success, data=None, message="", error=None, status_code=200
#     ):
#         """Create standardized API response"""
#         response_data = {
#             "success": success,
#             "message": message,
#             "timestamp": datetime.now().isoformat(),
#         }

#         if data is not None:
#             response_data["data"] = data

#         if error:
#             response_data["error"] = error

#         return http.Response(
#             json.dumps(response_data, default=str),
#             status=status_code,
#             content_type="application/json",
#         )

#     # Product API Endpoints
#     @http.route(
#         "/api/v1/products/create",
#         type="json",
#         auth="none",
#         methods=["POST"],
#         csrf=False,
#     )
#     def create_product(self, **kwargs):
#         """
#         Create a new product in Odoo
#         Expected JSON payload:
#         {
#             "name": "Product Name",
#             "default_code": "PROD-001",
#             "type": "product",
#             "tracking": "lot",
#             "uom_id": 1,
#             "uom_po_id": 1,
#             "categ_id": 1,
#             "list_price": 100.0,
#             "standard_price": 80.0
#         }
#         """
#         import json

#         # Authenticate
#         user = self._authenticate_request()
#         if not user:
#             return {
#                 "success": False,
#                 "error": "Authentication failed",
#                 "message": "Invalid or missing API key/Token",
#             }

#         try:
#             # Get request data
#             data = request.jsonrequest

#             # Validate required fields
#             if not data.get("name"):
#                 return {
#                     "success": False,
#                     "error": "Validation error",
#                     "message": "Product name is required",
#                 }

#             # Prepare product data
#             product_vals = {
#                 "name": data.get("name"),
#                 "default_code": data.get("default_code"),
#                 "type": data.get("type", "product"),
#                 "tracking": data.get("tracking", "none"),
#                 "uom_id": data.get("uom_id", 1),
#                 "uom_po_id": data.get("uom_po_id", data.get("uom_id", 1)),
#                 "categ_id": data.get("categ_id"),
#                 "list_price": data.get("list_price", 0.0),
#                 "standard_price": data.get("standard_price", 0.0),
#                 "sale_ok": data.get("sale_ok", True),
#                 "purchase_ok": data.get("purchase_ok", True),
#             }

#             # Remove None values
#             product_vals = {k: v for k, v in product_vals.items() if v is not None}

#             # Create product
#             product = request.env["product.product"].sudo(user.id).create(product_vals)

#             _logger.info(f"Product created: {product.id} - {product.name}")

#             return {
#                 "success": True,
#                 "message": f"Product created successfully",
#                 "data": {
#                     "product_id": product.id,
#                     "name": product.name,
#                     "default_code": product.default_code,
#                     "type": product.type,
#                 },
#             }

#         except ValidationError as ve:
#             _logger.error(f"Validation error creating product: {str(ve)}")
#             return {"success": False, "error": "Validation error", "message": str(ve)}
#         except Exception as e:
#             _logger.error(f"Error creating product: {str(e)}")
#             return {
#                 "success": False,
#                 "error": "Internal server error",
#                 "message": str(e),
#             }

#     @http.route(
#         "/api/v1/products/search_or_create",
#         type="json",
#         auth="none",
#         methods=["POST"],
#         csrf=False,
#     )
#     def search_or_create_product(self, **kwargs):
#         """
#         Search for product by default_code or name, create if not found
#         This matches the logic from the user's JavaScript example
#         """
#         import json

#         # Authenticate
#         user = self._authenticate_request()
#         if not user:
#             return {
#                 "success": False,
#                 "error": "Authentication failed",
#                 "message": "Invalid or missing API key/Token",
#             }

#         try:
#             data = request.jsonrequest
#             default_code = data.get("default_code")
#             name = data.get("name")
#             unit = data.get("unit", "Units")

#             if not name:
#                 return {
#                     "success": False,
#                     "error": "Validation error",
#                     "message": "Product name is required",
#                 }

#             # Search by default_code first
#             product_id = None
#             if default_code:
#                 products = (
#                     request.env["product.product"]
#                     .sudo(user.id)
#                     .search([("default_code", "=", default_code)], limit=1)
#                 )
#                 if products:
#                     product_id = products.id
#                     _logger.info(
#                         f"Found product by code: {default_code} (ID: {product_id})"
#                     )

#             # Search by name if not found by code
#             if not product_id:
#                 products = (
#                     request.env["product.product"]
#                     .sudo(user.id)
#                     .search([("name", "=", name)], limit=1)
#                 )
#                 if products:
#                     product_id = products.id
#                     _logger.info(f"Found product by name: {name} (ID: {product_id})")

#             # Create product if not found
#             if not product_id:
#                 # Find UoM
#                 uom_name = self._map_uom(unit)
#                 uom = (
#                     request.env["uom.uom"]
#                     .sudo(user.id)
#                     .search([("name", "=", uom_name)], limit=1)
#                 )
#                 uom_id = uom.id if uom else 1

#                 product_vals = {
#                     "name": name,
#                     "type": "product",
#                     "tracking": "lot",
#                     "uom_id": uom_id,
#                     "uom_po_id": uom_id,
#                 }

#                 if default_code:
#                     product_vals["default_code"] = default_code

#                 product = (
#                     request.env["product.product"].sudo(user.id).create(product_vals)
#                 )
#                 product_id = product.id
#                 _logger.info(
#                     f"Created product: {name} | Code: {default_code} (ID: {product_id})"
#                 )

#             return {
#                 "success": True,
#                 "message": "Product processed successfully",
#                 "data": {
#                     "product_id": product_id,
#                     "name": name,
#                     "default_code": default_code,
#                 },
#             }

#         except Exception as e:
#             _logger.error(f"Error in search_or_create_product: {str(e)}")
#             return {
#                 "success": False,
#                 "error": "Internal server error",
#                 "message": str(e),
#             }

#     def _map_uom(self, unit_name):
#         """Map unit name to Odoo UoM"""
#         mapping = {
#             "Unit": "Units",
#             "Set": "Units",
#             "Pair": "Units",
#         }
#         return mapping.get(unit_name, "Units")

#     # Stock Move API
#     @http.route(
#         "/api/v1/stock/moves/create",
#         type="json",
#         auth="none",
#         methods=["POST"],
#         csrf=False,
#     )
#     def create_stock_move(self, **kwargs):
#         """
#         Create a stock move
#         Expected JSON payload:
#         {
#             "product_id": 1,
#             "qty": 10,
#             "location_id": 8,
#             "location_dest_id": 12,
#             "picking_type_id": 1,
#             "reference": "MOV-001",
#             "lot_id": 1
#         }
#         """
#         import json

#         user = self._authenticate_request()
#         if not user:
#             return {
#                 "success": False,
#                 "error": "Authentication failed",
#                 "message": "Invalid or missing API key/Token",
#             }

#         try:
#             data = request.jsonrequest

#             # Validate required fields
#             required_fields = ["product_id", "qty", "location_id", "location_dest_id"]
#             for field in required_fields:
#                 if not data.get(field):
#                     return {
#                         "success": False,
#                         "error": "Validation error",
#                         "message": f"{field} is required",
#                     }

#             # Prepare stock move values
#             move_vals = {
#                 "product_id": data["product_id"],
#                 "product_uom_qty": data["qty"],
#                 "location_id": data["location_id"],
#                 "location_dest_id": data["location_dest_id"],
#                 "name": data.get(
#                     "reference", f'API Move {datetime.now().strftime("%Y%m%d%H%M%S")}'
#                 ),
#                 "picking_type_id": data.get("picking_type_id"),
#                 "lot_id": data.get("lot_id"),
#                 "state": "draft",
#             }

#             # Create stock move
#             move = request.env["stock.move"].sudo(user.id).create(move_vals)

#             # Validate and confirm the move
#             move._action_confirm()
#             move._action_assign()

#             _logger.info(f"Stock move created: {move.id}")

#             return {
#                 "success": True,
#                 "message": "Stock move created successfully",
#                 "data": {
#                     "move_id": move.id,
#                     "reference": move.reference or move.name,
#                     "state": move.state,
#                     "product_id": move.product_id.id,
#                     "qty": move.product_uom_qty,
#                 },
#             }

#         except ValidationError as ve:
#             _logger.error(f"Validation error creating stock move: {str(ve)}")
#             return {"success": False, "error": "Validation error", "message": str(ve)}
#         except Exception as e:
#             _logger.error(f"Error creating stock move: {str(e)}")
#             return {
#                 "success": False,
#                 "error": "Internal server error",
#                 "message": str(e),
#             }

#     # Manufacturing Order API
#     @http.route(
#         "/api/v1/mrp/production/create",
#         type="json",
#         auth="none",
#         methods=["POST"],
#         csrf=False,
#     )
#     def create_manufacturing_order(self, **kwargs):
#         """
#         Create a manufacturing order
#         Expected JSON payload:
#         {
#             "product_id": 1,
#             "product_qty": 10,
#             "bom_id": 1,
#             "location_src_id": 8,
#             "location_dest_id": 12,
#             "lot_id": 1,
#             "origin": "API Order"
#         }
#         """
#         import json

#         user = self._authenticate_request()
#         if not user:
#             return {
#                 "success": False,
#                 "error": "Authentication failed",
#                 "message": "Invalid or missing API key/Token",
#             }

#         try:
#             data = request.jsonrequest

#             # Validate required fields
#             if not data.get("product_id"):
#                 return {
#                     "success": False,
#                     "error": "Validation error",
#                     "message": "product_id is required",
#                 }

#             # Prepare manufacturing order values
#             mo_vals = {
#                 "product_id": data["product_id"],
#                 "product_qty": data.get("product_qty", 1),
#                 "bom_id": data.get("bom_id"),
#                 "location_src_id": data.get("location_src_id"),
#                 "location_dest_id": data.get("location_dest_id"),
#                 "lot_producing_id": data.get("lot_id"),
#                 "origin": data.get(
#                     "origin", f'API MO {datetime.now().strftime("%Y%m%d%H%M%S")}'
#                 ),
#             }

#             # Create manufacturing order
#             mo = request.env["mrp.production"].sudo(user.id).create(mo_vals)

#             # Generate moves
#             mo._onchange_product_id()
#             mo._onchange_bom_id()
#             mo._onchange_move_raw()
#             mo._onchange_move_finished()

#             _logger.info(f"Manufacturing order created: {mo.id}")

#             return {
#                 "success": True,
#                 "message": "Manufacturing order created successfully",
#                 "data": {
#                     "mo_id": mo.id,
#                     "name": mo.name,
#                     "product_id": mo.product_id.id,
#                     "product_qty": mo.product_qty,
#                     "state": mo.state,
#                     "origin": mo.origin,
#                 },
#             }

#         except ValidationError as ve:
#             _logger.error(f"Validation error creating manufacturing order: {str(ve)}")
#             return {"success": False, "error": "Validation error", "message": str(ve)}
#         except Exception as e:
#             _logger.error(f"Error creating manufacturing order: {str(e)}")
#             return {
#                 "success": False,
#                 "error": "Internal server error",
#                 "message": str(e),
#             }

#     # Stock Quant by Lot API
#     @http.route(
#         "/api/v1/stock/quant/by_lot",
#         type="json",
#         auth="none",
#         methods=["POST"],
#         csrf=False,
#     )
#     def create_stock_quant_by_lot(self, **kwargs):
#         """
#         Create or update stock quant by lot
#         This matches the logic from the user's JavaScript example
#         Expected JSON payload:
#         {
#             "product_id": 1,
#             "lot_id": 1,
#             "qty": 100,
#             "location_id": 8
#         }
#         """
#         import json

#         user = self._authenticate_request()
#         if not user:
#             return {
#                 "success": False,
#                 "error": "Authentication failed",
#                 "message": "Invalid or missing API key/Token",
#             }

#         try:
#             data = request.jsonrequest

#             # Validate required fields
#             required_fields = ["product_id", "lot_id", "qty"]
#             for field in required_fields:
#                 if not data.get(field):
#                     return {
#                         "success": False,
#                         "error": "Validation error",
#                         "message": f"{field} is required",
#                     }

#             product_id = data["product_id"]
#             lot_id = data["lot_id"]
#             qty = data["qty"]
#             location_id = data.get("location_id")

#             # Search for existing quant
#             domain = [
#                 ("product_id", "=", product_id),
#                 ("lot_id", "=", lot_id),
#                 ("location_id.usage", "=", "internal"),
#             ]

#             if location_id:
#                 domain.append(("location_id", "=", location_id))

#             quant = request.env["stock.quant"].sudo(user.id).search(domain, limit=1)

#             if quant:
#                 # Update existing quant
#                 quant.write({"inventory_quantity": qty})
#                 quant.action_apply_inventory()
#                 _logger.info(f"Updated stock quant: {quant.id} qty: {qty}")
#             else:
#                 # Get default location if not provided
#                 if not location_id:
#                     warehouse = (
#                         request.env["stock.warehouse"].sudo(user.id).search([], limit=1)
#                     )
#                     location_id = (
#                         warehouse.lot_stock_id.id if warehouse.lot_stock_id else 8
#                     )

#                 # Create new quant
#                 quant_vals = {
#                     "product_id": product_id,
#                     "lot_id": lot_id,
#                     "location_id": location_id,
#                     "inventory_quantity": qty,
#                 }

#                 quant = request.env["stock.quant"].sudo(user.id).create(quant_vals)
#                 quant.action_apply_inventory()
#                 _logger.info(f"Created stock quant: {quant.id} qty: {qty}")

#             return {
#                 "success": True,
#                 "message": "Stock quant processed successfully",
#                 "data": {
#                     "quant_id": quant.id,
#                     "product_id": product_id,
#                     "lot_id": lot_id,
#                     "qty": qty,
#                     "location_id": quant.location_id.id,
#                 },
#             }

#         except ValidationError as ve:
#             _logger.error(f"Validation error creating stock quant: {str(ve)}")
#             return {"success": False, "error": "Validation error", "message": str(ve)}
#         except Exception as e:
#             _logger.error(f"Error creating stock quant: {str(e)}")
#             return {
#                 "success": False,
#                 "error": "Internal server error",
#                 "message": str(e),
#             }

#     # Comprehensive sync endpoint matching the JavaScript example
#     @http.route(
#         "/api/v1/sync/product_by_lot",
#         type="json",
#         auth="none",
#         methods=["POST"],
#         csrf=False,
#     )
#     def sync_product_by_lot(self, **kwargs):
#         """
#         Comprehensive sync endpoint that matches the user's JavaScript example
#         Expected JSON payload:
#         {
#             "part_no": "PART-001",
#             "product_code": "PROD-001",
#             "qty": 100,
#             "unit": "Units",
#             "lot_no": "LOT-001",
#             "status": "done"
#         }
#         """
#         user = self._authenticate_request()
#         if not user:
#             return {
#                 "success": False,
#                 "error": "Authentication failed",
#                 "message": "Invalid or missing API key/Token",
#             }

#         try:
#             data = request.jsonrequest

#             # Validate required fields
#             required_fields = ["part_no", "lot_no", "qty"]
#             for field in required_fields:
#                 if not data.get(field):
#                     return {
#                         "success": False,
#                         "error": "Validation error",
#                         "message": f"{field} is required",
#                     }

#             # Check status (only sync when status = "done")
#             status = data.get("status")
#             if status != "done":
#                 return {
#                     "success": True,
#                     "message": f'Skipped - Status is "{status}", not "done"',
#                     "data": {
#                         "skipped": True,
#                         "reason": f'Status is "{status}", not "done"',
#                     },
#                 }

#             part_no = data["part_no"]
#             product_code = data.get("product_code")
#             qty = data["qty"]
#             unit = data.get("unit", "Units")
#             lot_no = data["lot_no"]

#             _logger.info(f"=== FG/PL/Production → Odoo Sync ===")
#             _logger.info(f"PART No.: {part_no}")
#             _logger.info(f"Product code: {product_code}")
#             _logger.info(f"QTY: {qty}")
#             _logger.info(f"Unit: {unit}")
#             _logger.info(f"Lot: {lot_no}")
#             _logger.info(f"Status: {status}")

#             # Step 1: Search or Create Product
#             product_id = None
#             if product_code:
#                 products = (
#                     request.env["product.product"]
#                     .sudo(user.id)
#                     .search([("default_code", "=", product_code)], limit=1)
#                 )
#                 if products:
#                     product_id = products.id
#                     _logger.info(
#                         f"Found product by code: {product_code} (ID: {product_id})"
#                     )

#             if not product_id:
#                 products = (
#                     request.env["product.product"]
#                     .sudo(user.id)
#                     .search([("name", "=", part_no)], limit=1)
#                 )
#                 if products:
#                     product_id = products.id
#                     _logger.info(f"Found product by name: {part_no} (ID: {product_id})")

#             if not product_id:
#                 # Find UoM
#                 uom_name = self._map_uom(unit)
#                 uom = (
#                     request.env["uom.uom"]
#                     .sudo(user.id)
#                     .search([("name", "=", uom_name)], limit=1)
#                 )
#                 uom_id = uom.id if uom else 1

#                 product_vals = {
#                     "name": part_no,
#                     "type": "product",
#                     "tracking": "lot",
#                     "uom_id": uom_id,
#                     "uom_po_id": uom_id,
#                 }

#                 if product_code:
#                     product_vals["default_code"] = product_code

#                 product = (
#                     request.env["product.product"].sudo(user.id).create(product_vals)
#                 )
#                 product_id = product.id
#                 _logger.info(
#                     f"Created product: {part_no} | Code: {product_code} (ID: {product_id})"
#                 )

#             # Step 2: Get company_id
#             company = request.env["res.company"].sudo(user.id).search([], limit=1)
#             company_id = company.id if company else 1

#             # Step 3: Search or Create Lot
#             lot = (
#                 request.env["stock.lot"]
#                 .sudo(user.id)
#                 .search(
#                     [("name", "=", lot_no), ("product_id", "=", product_id)], limit=1
#                 )
#             )

#             if lot:
#                 lot_id = lot.id
#                 _logger.info(f"Found existing lot: {lot_no} (ID: {lot_id})")
#             else:
#                 lot = (
#                     request.env["stock.lot"]
#                     .sudo(user.id)
#                     .create(
#                         {
#                             "name": lot_no,
#                             "product_id": product_id,
#                             "company_id": company_id,
#                         }
#                     )
#                 )
#                 lot_id = lot.id
#                 _logger.info(f"Created lot: {lot_no} (ID: {lot_id})")

#             # Step 4: Update stock quantity
#             quant = (
#                 request.env["stock.quant"]
#                 .sudo(user.id)
#                 .search(
#                     [
#                         ("product_id", "=", product_id),
#                         ("lot_id", "=", lot_id),
#                         ("location_id.usage", "=", "internal"),
#                     ],
#                     limit=1,
#                 )
#             )

#             if quant:
#                 quant.write({"inventory_quantity": qty})
#                 quant.action_apply_inventory()
#                 _logger.info(f"Updated stock qty: {qty}")
#             else:
#                 # Get default warehouse stock location
#                 warehouse = (
#                     request.env["stock.warehouse"].sudo(user.id).search([], limit=1)
#                 )
#                 location_id = warehouse.lot_stock_id.id if warehouse.lot_stock_id else 8

#                 quant = (
#                     request.env["stock.quant"]
#                     .sudo(user.id)
#                     .create(
#                         {
#                             "product_id": product_id,
#                             "lot_id": lot_id,
#                             "location_id": location_id,
#                             "inventory_quantity": qty,
#                         }
#                     )
#                 )
#                 quant.action_apply_inventory()
#                 _logger.info(f"Created stock quant (ID: {quant.id}) qty: {qty}")

#             _logger.info(f"=== ✅ Sync Complete ===")
#             _logger.info(
#                 f"Product: {part_no} | Code: {product_code} | Lot: {lot_no} | Qty: {qty} | Unit: {unit}"
#             )

#             return {
#                 "success": True,
#                 "message": "Sync completed successfully",
#                 "data": {
#                     "product_id": product_id,
#                     "lot_id": lot_id,
#                     "part_no": part_no,
#                     "product_code": product_code,
#                     "lot_no": lot_no,
#                     "qty": qty,
#                     "status": "success",
#                 },
#             }

#         except ValidationError as ve:
#             _logger.error(f"Validation error in sync: {str(ve)}")
#             return {"success": False, "error": "Validation error", "message": str(ve)}
#         except Exception as e:
#             _logger.error(f"Error in sync: {str(e)}")
#             return {
#                 "success": False,
#                 "error": "Internal server error",
#                 "message": str(e),
#             }

# import requests

# BASE_URL = "https://app.teable.ai/api"
# TOKEN = "YOUR_TOKEN"
# HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# TABLES = {
#     "products":   "tblP379MWmenn4nuya6",
#     "categories": "tbldtJiNl5zoUXgn01q",
#     "mo":         "tblyLHH8ca6Lh4IuuME",
#     "bom":        "tbl8YZUr6buCjNZJocD",
#     "bom_line":   "tblW14bhA1jxvxR6Ub1",
# }

# def get_records(table_key, filter_obj=None, take=100):
#     params = {
#         "fieldKeyType": "name",
#         "cellFormat": "text",
#         "take": take,
#     }
#     if filter_obj:
#         import json
#         params["filter"] = json.dumps(filter_obj)
    
#     resp = requests.get(
#         f"{BASE_URL}/table/{TABLES[table_key]}/record",
#         headers=HEADERS,
#         params=params
#     )
#     return resp.json()["records"]

# # Get all products
# products = get_records("products")

# # Get products filtered by category name
# products_filtered = get_records("products", {
#     "conjunction": "and",
#     "filterSet": [{
#         "fieldId": "fldIpARcWRibp1kwLs2",  # Category field
#         "operator": "is",
#         "value": "Finished Goods"
#     }]
# })

# # Get all MOs
# mos = get_records("mo")

# # Get all BOMs
# boms = get_records("bom")

# for p in products:
#     print(p["fields"])
