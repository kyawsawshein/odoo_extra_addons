import datetime
import json
import logging
from datetime import datetime
from typing import Dict

import requests
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# import jwt


_logger = logging.getLogger(__name__)


class ApiConfig(models.Model):
    _name = "api.config"
    _description = "API Configuration"

    name = fields.Char(string="Configuration Name", required=True)
    api_url = fields.Char(
        string="API Base URL", required=True, default="http://localhost:8000"
    )
    auth_url = fields.Char(
        string="Authentication URL",
        default="http://localhost:8000/api/v1/auth/token",
    )
    graphql_url = fields.Char(
        string="GraphQL URL", default="http://localhost:8000/graphql"
    )
    database = fields.Char(string="Database")
    token_key = fields.Char(string="Access Token Key")
    username = fields.Char(string="Username")
    password = fields.Char(string="Password")
    active = fields.Boolean(string="Active", default=True)
    token = fields.Char(string="Access Token", readonly=True)
    token_expiry = fields.Datetime(string="Token Expiry", readonly=True)

    # JWT Authentication settings
    enable_jwt_auth = fields.Boolean(string="Enable JWT Authentication", default=False)
    jwt_secret = fields.Char(
        string="JWT Secret Key", help="Secret key for JWT token verification"
    )
    jwt_algorithm = fields.Selection(
        [
            ("HS256", "HS256"),
            ("HS384", "HS384"),
            ("HS512", "HS512"),
            ("RS256", "RS256"),
        ],
        string="JWT Algorithm",
        default="HS256",
    )
    issuer = fields.Char(
        string="JWT ISSUER Key", help="Issuer key for JWT token verification"
    )
    audience = fields.Char(
        string="JWT AUDIENCE Key", help="Audience key for JWT token verification"
    )

    # Sync settings
    sync_contacts = fields.Boolean(string="Sync Contacts", default=True)
    sync_products = fields.Boolean(string="Sync Products", default=True)
    sync_interval = fields.Integer(string="Sync Interval (minutes)", default=60)
    last_sync_date = fields.Datetime(string="Last Sync Date", readonly=True)

    _sql_constraints = [
        ("name_unique", "unique(name)", "Configuration name must be unique!"),
    ]

    # def generate_token(self, uid: int) -> str:
    #     payload = {
    #         "uid": uid,
    #         "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    #         "iss": self.issuer,
    #         "aud": self.audience,
    #     }
    #     return jwt.encode(payload=payload, key=self.jwt_secret, algorithm=self.jwt_algorithm)

    # def decode_token(self, token: str) -> Dict[str, str]:
    #     return jwt.decode(
    #         jwt=token,
    #         key=self.jwt_secret,
    #         algorithms=self.jwt_algorithm,
    #         audience=self.audience,
    #         issuer=self.issuer,
    #     )

    @api.constrains("sync_interval")
    def _check_sync_interval(self):
        for record in self:
            if record.sync_interval < 1:
                raise ValidationError("Sync interval must be at least 1 minute")

    def authenticate(self):
        """Authenticate with the API and get access token"""
        try:
            auth_data = {"username": self.username, "password": self.password}
            _logger.info(f"Attempting authentication with URL: {self.auth_url}")

            response = requests.post(self.auth_url, data=auth_data, timeout=30)

            if response.status_code == 200:
                token_data = response.json()
                self.write(
                    {
                        "token": token_data.get("access_token"),
                        "token_expiry": datetime.now(),
                    }
                )
                _logger.info(
                    f"Successfully authenticated with API for config: {self.name}"
                )
                return True
            else:
                _logger.error(
                    f"Authentication failed: {response.status_code} - {response.text}"
                )
                error_msg = f"Authentication failed (Status {response.status_code})"
                if response.status_code == 401:
                    error_msg += ": Invalid username or password"
                elif response.status_code == 404:
                    error_msg += ": Authentication endpoint not found. Check the URL."
                elif response.status_code >= 500:
                    error_msg += (
                        ": Server error. Please check if the API service is running."
                    )
                else:
                    error_msg += f": {response.text}"
                raise UserError(error_msg)

        except requests.exceptions.ConnectionError as e:
            _logger.error(f"Connection failed: {str(e)}")
            error_msg = f"Cannot connect to API at {self.auth_url}. "
            error_msg += "Please check:\n"
            error_msg += "1. Is the API service running?\n"
            error_msg += "2. Is the URL correct?\n"
            error_msg += "3. Is the port accessible?\n"
            error_msg += f"Error details: {str(e)}"
            raise UserError(error_msg)

        except requests.exceptions.Timeout as e:
            _logger.error(f"Request timeout: {str(e)}")
            raise UserError(
                f"Request timeout: The API server took too long to respond. Check if the service is running and accessible."
            )

        except requests.exceptions.RequestException as e:
            _logger.error(f"Authentication request failed: {str(e)}")
            raise UserError(f"Authentication request failed: {str(e)}")

    def execute_graphql_query(self, query, variables=None):
        """Execute GraphQL query with authentication"""
        if not self.token:
            self.authenticate()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

        payload = {"query": query, "variables": variables or {}}
        _logger.info(
            f"URL : {self.graphql_url}, Payload : {payload} , Header : {headers}"
        )
        try:
            response = requests.post(
                self.graphql_url, json=payload, headers=headers, timeout=60
            )
            _logger.info(f"Response : {response.json()}")
            if response.status_code == 401:  # Token expired
                self.authenticate()
                headers["Authorization"] = f"Bearer {self.token}"
                response = requests.post(
                    self.graphql_url, json=payload, headers=headers, timeout=60
                )

            if response.status_code == 200:
                return response.json()
            else:
                _logger.error(
                    f"GraphQL query failed: {response.status_code} - {response.text}"
                )
                raise UserError(
                    f"GraphQL query failed: {response.status_code} - {response.text}"
                )

        except requests.exceptions.RequestException as e:
            _logger.error(f"GraphQL request failed: {str(e)}")
            raise UserError(f"GraphQL request failed: {str(e)}")

    def sync_contacts_from_odoo(self):
        """Sync contacts from Odoo API"""
        if not self.sync_contacts:
            _logger.info("Contact sync is disabled")
            return {"success": False, "message": "Contact sync is disabled"}

        # query = """
        # mutation {
        #     sync_contacts_from_odoo {
        #         success
        #         message
        #         odoo_id
        #         local_id
        #         errors
        #     }
        # }
        # """
        query = """
        mutation {
            syncContactsFromOdoo {
                success
                message
                odooId
                localId
                errors
            }
        }
        """

        try:
            result = self.execute_graphql_query(query)
            _logger.info(f"Result : {result}")
            sync_result = result.get("data", {}).get("sync_contacts_from_odoo", {})
            _logger.info(f"Sync result {sync_result}")
            # Create sync job record
            self.env["sync.job"].create(
                {
                    "config_id": self.id,
                    "job_type": "contacts",
                    "status": "success" if sync_result.get("success") else "failed",
                    "message": sync_result.get("message", ""),
                    "records_processed": 1 if sync_result.get("success") else 0,
                    "errors": str(sync_result.get("errors", [])),
                }
            )

            self.write({"last_sync_date": datetime.now()})
            _logger.info(f"Contact sync completed: {sync_result.get('message')}")
            return sync_result

        except Exception as e:
            _logger.error(f"Contact sync failed: {str(e)}")
            # Create failed sync job record
            self.env["sync.job"].create(
                {
                    "config_id": self.id,
                    "job_type": "contacts",
                    "status": "failed",
                    "message": str(e),
                    "records_processed": 0,
                    "errors": str(e),
                }
            )
            return {"success": False, "message": str(e), "errors": [str(e)]}

    def sync_products_from_odoo(self):
        """Sync products from Odoo API"""
        if not self.sync_products:
            _logger.info("Product sync is disabled")
            return {"success": False, "message": "Product sync is disabled"}

        query = """
        mutation {
            sync_products_from_odoo {
                success
                message
                odoo_id
                local_id
                errors
            }
        }
        """

        try:
            result = self.execute_graphql_query(query)
            sync_result = result.get("data", {}).get("sync_products_from_odoo", {})

            # Create sync job record
            self.env["sync.job"].create(
                {
                    "config_id": self.id,
                    "job_type": "products",
                    "status": "success" if sync_result.get("success") else "failed",
                    "message": sync_result.get("message", ""),
                    "records_processed": 1 if sync_result.get("success") else 0,
                    "errors": str(sync_result.get("errors", [])),
                }
            )

            self.write({"last_sync_date": datetime.now()})
            _logger.info(f"Product sync completed: {sync_result.get('message')}")
            return sync_result

        except Exception as e:
            _logger.error(f"Product sync failed: {str(e)}")
            # Create failed sync job record
            self.env["sync.job"].create(
                {
                    "config_id": self.id,
                    "job_type": "products",
                    "status": "failed",
                    "message": str(e),
                    "records_processed": 0,
                    "errors": str(e),
                }
            )
            return {"success": False, "message": str(e), "errors": [str(e)]}

    def sync_all_data(self):
        """Sync all enabled data types"""
        results = {}

        if self.sync_contacts:
            results["contacts"] = self.sync_contacts_from_odoo()

        if self.sync_products:
            results["products"] = self.sync_products_from_odoo()

        return results

    @api.model
    def _cron_sync_contacts(self):
        """Cron method to sync contacts from all active configurations"""
        active_configs = self.search(
            [("active", "=", True), ("sync_contacts", "=", True)]
        )
        for config in active_configs:
            try:
                config.sync_contacts_from_odoo()
                _logger.info(f"Cron: Contact sync completed for {config.name}")
            except Exception as e:
                _logger.error(f"Cron: Contact sync failed for {config.name}: {str(e)}")

    @api.model
    def _cron_sync_products(self):
        """Cron method to sync products from all active configurations"""
        active_configs = self.search(
            [("active", "=", True), ("sync_products", "=", True)]
        )
        for config in active_configs:
            try:
                config.sync_products_from_odoo()
                _logger.info(f"Cron: Product sync completed for {config.name}")
            except Exception as e:
                _logger.error(f"Cron: Product sync failed for {config.name}: {str(e)}")

    @api.model
    def _cron_sync_all_data(self):
        """Cron method to sync all data from all active configurations"""
        active_configs = self.search([("active", "=", True)])
        for config in active_configs:
            try:
                config.sync_all_data()
                _logger.info(f"Cron: All data sync completed for {config.name}")
            except Exception as e:
                _logger.error(f"Cron: All data sync failed for {config.name}: {str(e)}")
