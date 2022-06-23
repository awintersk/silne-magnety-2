# -*- coding: utf-8 -*-
{
    'name': "invoice_customs",

    'summary': """
        Add customization to invoice report""",

    'author': "krnac@implemento.sk",
    'website': "https://implemento.sk",

    'category': 'Uncategorized',
    'version': '14.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['woo_commerce_ept', 'sk_invoice', 'web', 'account'],

    # always loaded
    'data': [
        'views/woo_settings.xml',
        'views/report_invoice.xml',
    ],
}
