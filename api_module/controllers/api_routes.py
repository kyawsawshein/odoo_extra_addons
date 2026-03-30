
# """API Routes for external data access with authentication"""

# from odoo import http
# from odoo.http import request
# import json
# import logging
# from datetime import datetime

# _logger = logging.getLogger(__name__)


# class ApiModuleRoutes(http.Controller):

#     # Authentication methods
#     def _authenticate_api_key(self, api_key):
#         """Authenticate using API key"""
#         if not api_key:
#             return None
            
#         # Find API token in database
#         api_token = request.env['api.token'].sudo().search([
#             ('token', '=', api_key),
#             ('is_active', '=', True)
#         ], limit=1)
        
#         if api_token and api_token.expires_at and api_token.expires_at < datetime.now():
#             return None
            
#         return api_token

#     def _authenticate_user_password(self, username, password):
#         """Authenticate using username and password"""
#         if not username or not password:
#             return None
            
#         # Find user and verify password
#         user = request.env['res.users'].sudo().search([
#             ('login', '=', username)
#         ], limit=1)
        
#         if user and user._check_credentials(password):
#             return user
            
#         return None

#     def _authenticate_request(self):
#         """Authenticate request using API key or user/password"""
#         # Check for API key in headers
#         api_key = request.httprequest.headers.get('X-API-Key')
#         if api_key:
#             auth_result = self._authenticate_api_key(api_key)
#             if auth_result:
#                 return auth_result.user_id

#         # Check for Basic Auth
#         auth_header = request.httprequest.headers.get('Authorization')
#         if auth_header and auth_header.startswith('Basic '):
#             import base64
#             try:
#                 auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
#                 username, password = auth_decoded.split(':', 1)
#                 auth_result = self._authenticate_user_password(username, password)
#                 if auth_result:
#                     return auth_result
#             except Exception as e:
#                 _logger.error(f"Basic auth decoding failed: {str(e)}")

#         return None

#     def _create_response(self, success, data=None, message="", error=None, status_code=200):
#         """Create standardized API response"""
#         response_data = {
#             'success': success,
#             'message': message,
#             'timestamp': datetime.now().isoformat()
#         }
        
#         if data is not None:
#             response_data['data'] = data
            
#         if error:
#             response_data['error'] = error
            
#         return http.Response(
#             json.dumps(response_data, default=str),
#             status=status_code,
#             content_type='application/json'
#         )

#     # Product Routes
#     @http.route('/api/v1/products', type='http', auth='none', methods=['GET'], csrf=False)
#     def get_products(self, **kwargs):
#         """Get products with filtering and pagination"""
#         user = self._authenticate_request()
#         if not user:
#             return self._create_response(False, error="Authentication failed", status_code=401)

#         try:
#             # Parse query parameters
#             limit = int(kwargs.get('limit', 100))
#             offset = int(kwargs.get('offset', 0))
#             search = kwargs.get('search', '')
            
#             # Build domain for search
#             domain = []
#             if search:
#                 domain.append(('name', 'ilike', search))
                
#             # Get products
#             products = request.env['product.product'].sudo().search(
#                 domain, limit=limit, offset=offset
#             )
            
#             # Format response
#             product_data = []
#             for product in products:
#                 product_data.append({
#                     'id': product.id,
#                     'name': product.name,
#                     'default_code': product.default_code,
#                     'list_price': product.list_price,
#                     'standard_price': product.standard_price,
#                     'type': product.type,
#                     'categ_id': product.categ_id.id if product.categ_id else None,
#                     'categ_name': product.categ_id.name if product.categ_id else None,
#                     'uom_id': product.uom_id.id if product.uom_id else None,
#                     'uom_name': product.uom_id.name if product.uom_id else None,
#                     'active': product.active,
#                     'create_date': product.create_date.isoformat() if product.create_date else None,
#                     'write_date': product.write_date.isoformat() if product.write_date else None
#                 })
            
#             return self._create_response(
#                 True, 
#                 data={
#                     'products': product_data,
#                     'total': len(products),
#                     'limit': limit,
#                     'offset': offset
#                 },
#                 message=f"Found {len(products)} products"
#             )
            
#         except Exception as e:
#             _logger.error(f"Get products failed: {str(e)}")
#             return self._create_response(False, error=str(e), status_code=500)

#     @http.route('/api/v1/products', type='json', auth='none', methods=['POST'], csrf=False)
#     def create_product(self, **kwargs):
#         """Create a new product"""
#         user = self._authenticate_request()
#         if not user:
#             return {'success': False, 'error': 'Authentication failed'}

#         try:
#             product_data = request.jsonrequest
            
#             # Validate required fields
#             required_fields = ['name']
#             for field in required_fields:
#                 if field not in product_data:
#                     return {
#                         'success': False,
#                         'error': f'Missing required field: {field}'
#                     }

#             # Create product
#             product = request.env['product.product'].sudo().create({
#                 'name': product_data['name'],
#                 'default_code': product_data.get('default_code'),
#                 'list_price': product_data.get('list_price', 0.0),
#                 'standard_price': product_data.get('standard_price', 0.0),
#                 'type': product_data.get('type', 'product'),
#                 'categ_id': product_data.get('categ_id'),
#                 'uom_id': product_data.get('uom_id'),
#                 'active': product_data.get('active', True)
#             })

#             _logger.info(f"Product created: {product.id} by user {user.id}")

#             return {
#                 'success': True,
#                 'message': 'Product created successfully',
#                 'data': {
#                     'id': product.id,
#                     'name': product.name
#                 }
#             }
            
#         except Exception as e:
#             _logger.error(f"Create product failed: {str(e)}")
#             return {'success': False, 'error': str(e)}

#     # Contact Routes
#     @http.route('/api/v1/contacts', type='http', auth='none', methods=['GET'], csrf=False)
#     def get_contacts(self, **kwargs):
#         """Get contacts with filtering and pagination"""
#         user = self._authenticate_request()
#         if not user:
#             return self._create_response(False, error="Authentication failed", status_code=401)

#         try:
#             limit = int(kwargs.get('limit', 100))
#             offset = int(kwargs.get('offset', 0))
#             search = kwargs.get('search', '')
            
#             domain = []
#             if search:
#                 domain.append(('name', 'ilike', search))
                
#             contacts = request.env['res.partner'].sudo().search(
#                 domain, limit=limit, offset=offset
#             )
            
#             contact_data = []
#             for contact in contacts:
#                 contact_data.append({
#                     'id': contact.id,
#                     'name': contact.name,
#                     'email': contact.email,
#                     'phone': contact.phone,
#                     'street': contact.street,
#                     'city': contact.city,
#                     'country_id': contact.country_id.id if contact.country_id else None,
#                     'country_name': contact.country_id.name if contact.country_id else None,
#                     'is_company': contact.is_company,
#                     'company_type': contact.company_type,
#                     'active': contact.active,
#                     'create_date': contact.create_date.isoformat() if contact.create_date else None
#                 })
            
#             return self._create_response(
#                 True,
#                 data={
#                     'contacts': contact_data,
#                     'total': len(contacts),
#                     'limit': limit,
#                     'offset': offset
#                 },
#                 message=f"Found {len(contacts)} contacts"
#             )
            
#         except Exception as e:
#             _logger.error(f"Get contacts failed: {str(e)}")
#             return self._create_response(False, error=str(e), status_code=500)

#     @http.route('/api/v1/contacts', type='json', auth='none', methods=['POST'], csrf=False)
#     def create_contact(self, **kwargs):
#         """Create a new contact"""
#         user = self._authenticate_request()
#         if not user:
#             return {'success': False, 'error': 'Authentication failed'}

#         try:
#             contact_data = request.jsonrequest
            
#             if 'name' not in contact_data:
#                 return {
#                     'success': False,
#                     'error': 'Missing required field: name'
#                 }

#             contact = request.env['res.partner'].sudo().create({
#                 'name': contact_data['name'],
#                 'email': contact_data.get('email'),
#                 'phone': contact_data.get('phone'),
#                 'street': contact_data.get('street'),
#                 'city': contact_data.get('city'),
#                 'country_id': contact_data.get('country_id'),
#                 'is_company': contact_data.get('is_company', False),
#                 'company_type': contact_data.get('company_type', 'person')
#             })

#             _logger.info(f"Contact created: {contact.id} by user {user.id}")

#             return {
#                 'success': True,
#                 'message': 'Contact created successfully',
#                 'data': {
#                     'id': contact.id,
#                     'name': contact.name
#                 }
#             }
            
#         except Exception as e:
#             _logger.error(f"Create contact failed: {str(e)}")
#             return {'success': False, 'error': str(e)}

#     # Purchase Order Routes
#     @http.route('/api/v1/purchase-orders', type='http', auth='none', methods=['GET'], csrf=False)
#     def get_purchase_orders(self, **kwargs):
#         """Get purchase orders with filtering"""
#         user = self._authenticate_request()
#         if not user:
#             return self._create_response(False, error="Authentication failed", status_code=401)

#         try:
#             limit = int(kwargs.get('limit', 100))
#             offset = int(kwargs.get('offset', 0))
#             partner_id = kwargs.get('partner_id')
#             state = kwargs.get('state')
            
#             domain = []
#             if partner_id:
#                 domain.append(('partner_id', '=', int(partner_id)))
#             if state:
#                 domain.append(('state', '=', state))
                
#             orders = request.env['purchase.order'].sudo().search(
#                 domain, limit=limit, offset=offset, order='create_date desc'
#             )
            
#             order_data = []
#             for order in orders:
#                 order_data.append({
#                     'id': order.id,
#                     'name': order.name,
#                     'partner_id': order.partner_id.id,
#                     'partner_name': order.partner_id.name,
#                     'date_order': order.date_order.isoformat() if order.date_order else None,
#                     'state': order.state,
#                     'amount_total': order.amount_total,
#                     'currency_id': order.currency_id.id if order.currency_id else None,
#                     'currency_name': order.currency_id.name if order.currency_id else None,
#                     'create_date': order.create_date.isoformat() if order.create_date else None
#                 })
            
#             return self._create_response(
#                 True,
#                 data={
#                     'purchase_orders': order_data,
#                     'total': len(orders),
#                     'limit': limit,
#                     'offset': offset
#                 },
#                 message=f"Found {len(orders)} purchase orders"
#             )
            
#         except Exception as e:
#             _logger.error(f"Get purchase orders failed: {str(e)}")
#             return self._create_response(False, error=str(e), status_code=500)

#     # Sale Order Routes
#     @http.route('/api/v1/sale-orders', type='http', auth='none', methods=['GET'], csrf=False)
#     def get_sale_orders(self, **kwargs):
#         """Get sale orders with filtering"""
#         user = self._authenticate_request()
#         if not user:
#             return self._create_response(False, error="Authentication failed", status_code=401)

#         try:
#             limit = int(kwargs.get('limit', 100))
#             offset = int(kwargs.get('offset', 0))
#             partner_id = kwargs.get('partner_id')
#             state = kwargs.get('state')
            
#             domain = []
#             if partner_id:
#                 domain.append(('partner_id', '=', int(partner_id)))
#             if state:
#                 domain.append(('state', '=', state))
                
#             orders = request.env['sale.order'].sudo().search(
#                 domain, limit=limit, offset=offset, order='create_date desc'
#             )
            
#             order_data = []
#             for order in orders:
#                 order_data.append({
#                     'id': order.id,
#                     'name': order.name,
#                     'partner_id': order.partner_id.id,
#                     'partner_name': order.partner_id.name,
#                     'date_order': order.date_order.isoformat() if order.date_order else None,
#                     'state': order.state,
#                     'amount_total': order.amount_total,
#                     'currency_id': order.currency_id.id if order.currency_id else None,
#                     'currency_name': order.currency_id.name if order.currency_id else None,
#                     'create_date': order.create_date.isoformat() if order.create_date else None
#                 })
            
#             return self._create_response(
#                 True,
#                 data={
#                     'sale_orders': order_data,
#                     'total': len(orders),
#                     'limit': limit,
#                     'offset': offset
#                 },
#                 message=f"Found {len(orders)} sale orders"
#             )
            
#         except Exception as e:
#             _logger.error(f"Get sale orders failed: {str(e)}")
#             return self._create_response(False, error=str(e), status_code=500)

#     # Inventory Routes
#     @http.route('/api/v1/inventory', type='http', auth='none', methods=['GET'], csrf=False)
#     def get_inventory(self, **kwargs):
#         """Get inventory data"""
#         user = self._authenticate_request()
#         if not user:
#             return self._create_response(False, error="Authentication failed", status_code=401)

#         try:
#             product_id = kwargs.get('product_id')
#             location_id = kwargs.get('location_id')
            
#             domain = []
#             if product_id:
#                 domain.append(('product_id', '=', int(product_id)))
#             if location_id:
#                 domain.append(('location_id', '=', int(location_id)))
                
#             quants = request.env['stock.quant'].sudo().search(domain)
            
#             inventory_data = []
#             for quant in quants:
#                 inventory_data.append({
#                     'id': quant.id,
#                     'product_id': quant.product_id.id,
#                     'product_name': quant.product_id.name,
#                     'location_id': quant.location_id.id,
#                     'location_name': quant.location_id.complete_name,
#                     'quantity': quant.quantity,
#                     'reserved_quantity': quant.reserved_quantity,
#                     'available_quantity': quant.quantity - quant.reserved_quantity,
#                     'lot_id': quant.lot_id.id if quant.lot_id else None,
#                     'lot_name': quant.lot_id.name if quant.lot_id else None,
#                     'package_id': quant.package_id.id if quant.package_id else None
#                 })
            
#             return self._create_response(
#                 True,
#                 data={
#                     'inventory': inventory_data,
#                     'total': len(quants)
#                 },
#                 message=f"Found {len(quants)} inventory records"
#             )
            
#         except Exception as e:
#             _logger.error(f"Get inventory failed: {str(e)}")
#             return self._create_response(False, error=str(e), status_code=500)

#     # Invoice Routes
#     @http.route('/api/v1/invoices', type='http', auth='none', methods=['GET'], csrf=False)
#     def get_invoices(self, **kwargs):
#         """Get invoices with filtering"""
#         user = self._authenticate_request()
#         if not user:
#             return self._create_response(False, error="Authentication failed", status_code=401)

#         try:
#             limit = int(kwargs.get('limit', 100))
#             offset = int(kwargs.get('offset', 0))
#             partner_id = kwargs.get('partner_id')
#             state = kwargs.get('state')
#             invoice_type = kwargs.get('type', 'out_invoice')  # out_invoice or in_invoice
            
#             domain = [('move_type', '=', invoice_type)]
#             if partner_id:
#                 domain.append(('partner_id', '=', int(partner_id)))
#             if state:
#                 domain.append(('state', '=', state))
                
#             invoices = request.env['account.move'].sudo().search(
#                 domain, limit=limit, offset=offset, order='create_date desc'
#             )
            
#             invoice_data = []
#             for invoice in invoices:
#                 invoice_data.append({
#                     'id': invoice.id,
#                     'name': invoice.name,
#                     'partner_id': invoice.partner_id.id,
#                     'partner_name': invoice.partner_id.name,
#                     'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
#                     'state': invoice.state,
#                     'amount_total': invoice.amount_total,
#                     'amount_residual': invoice.amount_residual,
#                     'currency_id': invoice.currency_id.id if invoice.currency_id else None,
#                     'currency_name': invoice.currency_id.name if invoice.currency_id else None,
#                     'move_type': invoice.move_type,
#                     'create_date': invoice.create_date.isoformat() if invoice.create_date else None
#                 })
            
#             return self._create_response(
#                 True,
#                 data={
#                     'invoices': invoice_data,
#                     'total': len(invoices),
#                     'limit': limit,
#                     'offset': offset
#                 },
#                 message=f"Found {len(invoices)} invoices"
#             )
            
#         except Exception as e:
#             _logger.error(f"Get invoices failed: {str(e)}")
#             return self._create_response(False, error=str(e), status_code=500)

#     # Health check endpoint
#     @http.route('/api/v1/health', type='http', auth='none', methods=['GET'], csrf=False)
#     def health_check(self, **kwargs):
#         """Health check endpoint"""
#         return self._create_response(
#             True,
#             data={
#                 'status': 'healthy',
#                 'timestamp': datetime.now().isoformat(),
#                 'version': '1.0.0'
#             },
#             message="API is running"
#         )