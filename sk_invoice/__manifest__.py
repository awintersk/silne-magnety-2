# -*- coding: utf-8 -*-
{
    'name': "sk_invoice",

    'summary': """
        Base addon to extend contact fields with legal data, and report view""",

    'author': "krnac@implemento.sk",
    'website': "https://implemento.sk",

    'category': 'Uncategorized',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale'],

    # always loaded
    'data': [
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/report_invoice.xml',
        'views/report_quotations.xml',
        'views/account_move.xml',
    ],
}
