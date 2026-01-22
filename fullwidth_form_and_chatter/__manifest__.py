# -*- coding: utf-8 -*-
{
    "name": "FullWidth Form & Chatter",
    "author": "Odoo Hub",
    "category": "Tools",
    "summary": "FullWidth Form & Chatter provides an enhanced user experience by enabling a full-width form view,",
    "description": """
        The FullWidth Form & Chatter app allows users to customize their Odoo interface by setting form views.
    """,
    "maintainer": "Odoo Hub",
    "website": "https://apps.odoo.com/apps/modules/browse?author=Odoo%20Hub",
    "version": "1.1",
    "depends": ["base", "web", "mail"],
    "assets": {
        "web.assets_backend": [
            "fullwidth_form_and_chatter/static/src/**/*",
        ],
    },
    "images": ["static/description/banner.png"],
    "live_test_url": "https://youtu.be/OsfAW7la-5U",
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
