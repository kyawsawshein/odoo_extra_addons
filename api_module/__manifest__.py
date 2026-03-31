{
    "name": "API Integration Module",
    "version": "1.0",
    "summary": "Module for integrating with external API for data synchronization",
    "description": """
        This module provides integration with external API for syncing contacts and products.
        It includes automatic cron jobs for regular data synchronization.
    """,
    "category": "Tools",
    "author": "Your Company",
    "website": "https://www.yourcompany.com",
    "depends": ["base", "contacts", "product", "stock", "mrp"],
    "data": [
        "security/ir.model.access.csv",
        "views/api_config_views.xml",
        "views/sync_job_views.xml",
        "views/api_token_views.xml",
        "views/teable_ai_view.xml",
        "views/menu_views.xml",
        "data/cron_data.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
