# -*- coding: utf-8 -*-
{
    'name': "invoice_notes",

    'summary': """
        Add some legal notes into invoice based on customer location/vat payer""",

    'author': "krnac@implemento.sk",
    'website': "https://implemento.sk",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sk_invoice'],

    # always loaded
    'data': [
        'data/res_country_data.xml',
        'views/report_invoice.xml',
    ],
}
