# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Simple MRP",
    "summary": "Simple production",
    "version": "19.0.1.1.1",
    "author": "Zervi",
    "website": "https://www.globalzervi.com",
    "category": "Manufacturing",
    "depends": ["stock_account"],
    "license": "OPL-1",
    "data": [
        "data/sequence.xml",
        "security/groups.xml",
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "views/uom_conversion_views.xml",
        "views/product_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
