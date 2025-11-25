{
    "name": "Zervi Assets Management",
    "version": "1.0.0",
    "author": "Zervi",
    "depends": ["stock_account", "om_account_asset"],
    "description": """Manage assets owned by a company or a person. 
        Keeps track of depreciation's, and creates corresponding journal entries""",
    "summary": "Zervi Assets Management",
    "category": "Accounting",
    "sequence": 10,
    "website": "https://www.zerviglobal.com",
    'license': 'LGPL-3',
    "images": [],
    "data": [
        "data/account_asset_data.xml",
        "wizard/asset_depreciation_journal_wizard_views.xml",
        "wizard/asset_modify_views.xml",
        "views/account_asset_views.xml",
    ],
    "assets": {},
}
