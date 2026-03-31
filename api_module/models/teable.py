import datetime
import json
import logging
from datetime import datetime
from typing import Dict

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class Teable(models.Model):
    _name = "teable.ai"
    _description = "Teable AI"

    name = fields.Char(string="Table Name", required=True)
    table = fields.Char(string="Table ID", required=True)
