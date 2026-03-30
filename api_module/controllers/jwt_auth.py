# """JWT Authentication Controller for Odoo API Integration"""

# from odoo import http
# from odoo.http import request
# import json
# import logging
# import requests
# from datetime import datetime, timedelta
# import jwt
# from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
# import secrets
# import string

# import jwt

# from odoo import http, _  # type: ignore
# from odoo.http import request  # type: ignore
# from odoo.exceptions import ValidationError

# from .auth_route import AuthRoute


# _logger = logging.getLogger(__name__)


# from typing import Dict

# import datetime
# import jwt


# class JwtAuthController(http.Controller):
#     """Controller for JWT authentication with odoo_api"""

#     def __init__(self):
#         self.odoo_api_url = None
#         self.jwt_secret = None
#         self.jwt_algorithm = "HS256"
#         self._load_config()

#     def _load_config(self):
#         """Load JWT configuration from API config"""
#         try:
#             config = request.env['api.config'].sudo().search([
#                 ('active', '=', True),
#                 ('enable_jwt_auth', '=', True)
#             ], limit=1)
            
#             if config:
#                 self.odoo_api_url = config.api_url
#                 self.jwt_secret = config.jwt_secret
#                 self.jwt_algorithm = config.jwt_algorithm
#             else:
#                 _logger.warning("No active JWT configuration found")
#         except Exception as e:
#             _logger.error(f"Failed to load JWT config: {str(e)}")

#     def _verify_jwt_token(self, token):
#         """Verify JWT token from odoo_api"""
#         try:
#             if not self.jwt_secret:
#                 _logger.error("JWT secret not configured")
#                 return None

#             # Decode and verify JWT token
#             payload = jwt.decode(
#                 token, 
#                 self.jwt_secret, 
#                 algorithms=[self.jwt_algorithm]
#             )
            
#             # Check if token is expired
#             if 'exp' in payload and datetime.fromtimestamp(payload['exp']) < datetime.now():
#                 _logger.warning("JWT token expired")
#                 return None
                
#             return payload
            
#         except ExpiredSignatureError:
#             _logger.warning("JWT token expired")
#             return None
#         except InvalidTokenError as e:
#             _logger.error(f"Invalid JWT token: {str(e)}")
#             return None
#         except Exception as e:
#             _logger.error(f"JWT verification failed: {str(e)}")
#             return None

#     def _authenticate_with_odoo_api(self, username, password):
#         """Authenticate with odoo_api and get JWT token"""
#         try:
#             if not self.odoo_api_url:
#                 _logger.error("Odoo API URL not configured")
#                 return None

#             # Call odoo_api authentication endpoint
#             auth_url = f"{self.odoo_api_url.rstrip('/')}/api/v1/auth/token"
            
#             response = requests.post(
#                 auth_url,
#                 data={
#                     'username': username,
#                     'password': password,
#                     'grant_type': 'password'
#                 },
#                 headers={'Content-Type': 'application/x-www-form-urlencoded'},
#                 timeout=30
#             )

#             if response.status_code == 200:
#                 token_data = response.json()
#                 return token_data.get('access_token')
#             else:
#                 _logger.error(f"Odoo API authentication failed: {response.status_code} - {response.text}")
#                 return None

#         except requests.exceptions.RequestException as e:
#             _logger.error(f"Odoo API connection error: {str(e)}")
#             return None
#         except Exception as e:
#             _logger.error(f"Odoo API authentication error: {str(e)}")
#             return None

#     def _get_user_from_jwt(self, jwt_payload):
#         """Get or create Odoo user from JWT payload"""
#         try:
#             username = jwt_payload.get('sub')
#             user_id = jwt_payload.get('user_id')
            
#             if not username:
#                 return None

#             # Try to find existing user by username
#             user = request.env['res.users'].sudo().search([
#                 ('login', '=', username)
#             ], limit=1)

#             if user:
#                 return user

#             # If user doesn't exist, create a new one
#             # This is optional - you might want to only allow existing users
#             _logger.info(f"Creating new Odoo user from JWT: {username}")
            
#             user = request.env['res.users'].sudo().create({
#                 'name': username,
#                 'login': username,
#                 'password': 'jwt-authenticated-user',  # Random password since we use JWT
#                 'groups_id': [(4, request.env.ref('base.group_user').id)],
#                 'active': True
#             })
            
#             return user

#         except Exception as e:
#             _logger.error(f"Failed to get/create user from JWT: {str(e)}")
#             return None

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

#     def _generate_jwt_token(self, user_id, username, expires_hours=24):
#         """Generate JWT token for user"""
#         try:
#             if not self.jwt_secret:
#                 _logger.error("JWT secret not configured for token generation")
#                 return None

#             # Create payload
#             payload = {
#                 'sub': username,
#                 'user_id': user_id,
#                 'exp': datetime.now() + timedelta(hours=expires_hours),
#                 'iat': datetime.now(),
#                 'iss': 'odoo_api_module'
#             }

#             # Generate token
#             token = jwt.encode(
#                 payload,
#                 self.jwt_secret,
#                 algorithm=self.jwt_algorithm
#             )

#             return token

#         except Exception as e:
#             _logger.error(f"Failed to generate JWT token: {str(e)}")
#             return None

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

#     @http.route('/api/v1/auth/jwt/login', type='json', auth='none', methods=['POST'], csrf=False)
#     def jwt_login(self, **kwargs):
#         """Login using JWT token from odoo_api"""
#         try:
#             login_data = request.jsonrequest
            
#             # Check if we have JWT token directly
#             jwt_token = login_data.get('jwt_token')
#             if jwt_token:
#                 # Verify JWT token
#                 jwt_payload = self._verify_jwt_token(jwt_token)
#                 if jwt_payload:
#                     user = self._get_user_from_jwt(jwt_payload)
#                     if user:
#                         # Login the user in Odoo session
#                         request.session.authenticate(user.login, 'jwt-authenticated-user')
                        
#                         return {
#                             'success': True,
#                             'message': 'JWT authentication successful',
#                             'data': {
#                                 'user_id': user.id,
#                                 'username': user.login,
#                                 'name': user.name,
#                                 'session_id': request.session.sid
#                             }
#                         }
            
#             # If no JWT token, try username/password authentication with odoo_api
#             username = login_data.get('username')
#             password = login_data.get('password')
            
#             if username and password:
#                 # Get JWT token from odoo_api
#                 jwt_token = self._authenticate_with_odoo_api(username, password)
#                 if jwt_token:
#                     # Verify the token
#                     jwt_payload = self._verify_jwt_token(jwt_token)
#                     if jwt_payload:
#                         user = self._get_user_from_jwt(jwt_payload)
#                         if user:
#                             # Login the user in Odoo session
#                             request.session.authenticate(user.login, 'jwt-authenticated-user')
                            
#                             return {
#                                 'success': True,
#                                 'message': 'JWT authentication successful',
#                                 'data': {
#                                     'user_id': user.id,
#                                     'username': user.login,
#                                     'name': user.name,
#                                     'jwt_token': jwt_token,
#                                     'session_id': request.session.sid
#                                 }
#                             }

#             return {
#                 'success': False,
#                 'error': 'Authentication failed. Provide valid JWT token or username/password.'
#             }

#         except Exception as e:
#             _logger.error(f"JWT login failed: {str(e)}")
#             return {
#                 'success': False,
#                 'error': f'Authentication error: {str(e)}'
#             }

#     @http.route('/api/v1/auth/jwt/verify', type='json', auth='none', methods=['POST'], csrf=False)
#     def verify_jwt_token(self, **kwargs):
#         """Verify JWT token and get user information"""
#         try:
#             token_data = request.jsonrequest
#             jwt_token = token_data.get('jwt_token')
            
#             if not jwt_token:
#                 return {
#                     'success': False,
#                     'error': 'JWT token is required'
#                 }

#             jwt_payload = self._verify_jwt_token(jwt_token)
#             if jwt_payload:
#                 user = self._get_user_from_jwt(jwt_payload)
#                 if user:
#                     return {
#                         'success': True,
#                         'message': 'JWT token is valid',
#                         'data': {
#                             'user_id': user.id,
#                             'username': user.login,
#                             'name': user.name,
#                             'jwt_payload': jwt_payload
#                         }
#                     }
            
#             return {
#                 'success': False,
#                 'error': 'Invalid or expired JWT token'
#             }

#         except Exception as e:
#             _logger.error(f"JWT verification failed: {str(e)}")
#             return {
#                 'success': False,
#                 'error': f'Token verification error: {str(e)}'
#             }

#     @http.route('/api/v1/auth/jwt/logout', type='json', auth='user', methods=['POST'])
#     def jwt_logout(self, **kwargs):
#         """Logout current JWT-authenticated user"""
#         try:
#             # Clear the session
#             request.session.logout()
            
#             return {
#                 'success': True,
#                 'message': 'Logout successful'
#             }

#         except Exception as e:
#             _logger.error(f"JWT logout failed: {str(e)}")
#             return {
#                 'success': False,
#                 'error': f'Logout error: {str(e)}'
#             }

#     @http.route('/api/v1/auth/jwt/me', type='json', auth='user', methods=['GET'])
#     def get_current_user(self, **kwargs):
#         """Get current authenticated user information"""
#         try:
#             user = request.env.user
            
#             return {
#                 'success': True,
#                 'data': {
#                     'user_id': user.id,
#                     'username': user.login,
#                     'name': user.name,
#                     'email': user.email,
#                     'company_id': user.company_id.id,
#                     'company_name': user.company_id.name,
#                     'groups': [group.name for group in user.groups_id]
#                 }
#             }

#         except Exception as e:
#             _logger.error(f"Get current user failed: {str(e)}")
#             return {
#                 'success': False,
#                 'error': f'Failed to get user information: {str(e)}'
#             }

#     @http.route('/api/v1/auth/jwt/generate-token', type='json', auth='none', methods=['POST'], csrf=False)
#     def generate_jwt_token(self, **kwargs):
#         """Generate JWT token for authenticated Odoo user - called by odoo_api"""
#         try:
#             # Load configuration first
#             self._load_config()
            
#             if not self.jwt_secret:
#                 return {
#                     'success': False,
#                     'error': 'JWT authentication not configured'
#                 }

#             # Get authentication data from request
#             auth_data = request.jsonrequest
#             username = auth_data.get('username')
#             password = auth_data.get('password')
            
#             if not username or not password:
#                 return {
#                     'success': False,
#                     'error': 'Username and password are required'
#                 }

#             # Authenticate user with Odoo
#             user = self._authenticate_user_password(username, password)
#             if not user:
#                 return {
#                     'success': False,
#                     'error': 'Invalid username or password'
#                 }

#             # Generate JWT token
#             jwt_token = self._generate_jwt_token(user.id, user.login)
#             if not jwt_token:
#                 return {
#                     'success': False,
#                     'error': 'Failed to generate JWT token'
#                 }

#             # Return token data
#             return {
#                 'success': True,
#                 'message': 'JWT token generated successfully',
#                 'data': {
#                     'access_token': jwt_token,
#                     'token_type': 'bearer',
#                     'expires_in': 24 * 60 * 60,  # 24 hours in seconds
#                     'user_id': user.id,
#                     'username': user.login,
#                     'name': user.name
#                 }
#             }

#         except Exception as e:
#             _logger.error(f"JWT token generation failed: {str(e)}")
#             return {
#                 'success': False,
#                 'error': f'Token generation failed: {str(e)}'
#             }
