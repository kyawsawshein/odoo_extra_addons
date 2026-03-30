"""API Token model for external authentication"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import secrets
import json
from datetime import datetime, timedelta


class ApiToken(models.Model):
    _name = 'api.token'
    _description = 'API Token for external authentication'
    _rec_name = 'name'

    name = fields.Char(string='Token Name', required=True)
    token = fields.Char(string='API Token', required=True, copy=False)
    user_id = fields.Many2one(
        'res.users', 
        string='User', 
        required=True,
        default=lambda self: self.env.user.id
    )
    scopes = fields.Text(
        string='Allowed Scopes',
        help='JSON array of allowed API scopes',
        default='[]'
    )
    is_active = fields.Boolean(string='Active', default=True)
    created_at = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    expires_at = fields.Datetime(string='Expires At')
    
    _sql_constraints = [
        ('token_unique', 'unique(token)', 'API Token must be unique!'),
    ]

    @api.model
    def create(self, vals):
        """Generate unique token on creation"""
        if 'token' not in vals or not vals['token']:
            # Generate a secure random token
            vals['token'] = secrets.token_urlsafe(32)
        
        # Validate scopes format
        if 'scopes' in vals:
            try:
                json.loads(vals['scopes'])
            except (json.JSONDecodeError, TypeError):
                raise ValidationError("Scopes must be a valid JSON array")
        
        return super().create(vals)

    @api.constrains('scopes')
    def _check_scopes_format(self):
        """Validate scopes field is valid JSON"""
        for record in self:
            if record.scopes:
                try:
                    json.loads(record.scopes)
                except (json.JSONDecodeError, TypeError):
                    raise ValidationError("Scopes must be a valid JSON array")

    @api.constrains('expires_at')
    def _check_expires_at(self):
        """Validate expiration date is in the future"""
        for record in self:
            if record.expires_at and record.expires_at < datetime.now():
                raise ValidationError("Expiration date must be in the future")

    def is_valid(self):
        """Check if token is valid (active and not expired)"""
        self.ensure_one()
        if not self.is_active:
            return False
        
        if self.expires_at and self.expires_at < datetime.now():
            return False
            
        return True

    def get_scopes(self):
        """Get scopes as Python list"""
        try:
            return json.loads(self.scopes) if self.scopes else []
        except (json.JSONDecodeError, TypeError):
            return []

    def has_scope(self, scope):
        """Check if token has specific scope"""
        return scope in self.get_scopes()

    def renew_token(self, days=30):
        """Renew token expiration"""
        self.ensure_one()
        self.write({
            'expires_at': datetime.now() + timedelta(days=days)
        })
        return True

    def generate_new_token(self):
        """Generate a new token value"""
        self.ensure_one()
        self.write({
            'token': secrets.token_urlsafe(32),
            'created_at': fields.Datetime.now()
        })
        return self.token

    @api.model
    def validate_token(self, token, required_scopes=None):
        """Validate token and check scopes"""
        if not token:
            return None
            
        api_token = self.search([
            ('token', '=', token),
            ('is_active', '=', True)
        ], limit=1)
        
        if not api_token or not api_token.is_valid():
            return None
            
        # Check scopes if required
        if required_scopes:
            token_scopes = api_token.get_scopes()
            if not all(scope in token_scopes for scope in required_scopes):
                return None
                
        return api_token

    def action_renew(self):
        """Action to renew token for 30 days"""
        for record in self:
            record.renew_token(30)
        return True

    def action_generate_new(self):
        """Action to generate new token"""
        for record in self:
            record.generate_new_token()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'New Token Generated',
                'message': 'A new API token has been generated successfully.',
                'type': 'success',
                'sticky': False,
            }
        }