from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging
import requests
import json
from datetime import datetime

_logger = logging.getLogger(__name__)


class SyncJob(models.Model):
    _name = "sync.job"
    _description = "Sync Job History"
    _order = "create_date desc"

    config_id = fields.Many2one("api.config", string="API Configuration", required=True)
    job_type = fields.Selection(
        [("contacts", "Contacts"), ("products", "Products"), ("all", "All")],
        string="Job Type",
        required=True,
    )
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("running", "Running"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        string="Status",
        default="pending",
    )
    message = fields.Text(string="Message")
    records_processed = fields.Integer(string="Records Processed", default=0)
    errors = fields.Text(string="Errors")
    create_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    complete_date = fields.Datetime(string="Completed Date")
