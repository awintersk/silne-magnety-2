# -*- coding: utf-8 -*-
{
    'name': "Export Template for KROS system",

    'summary': """Export Template for KROS system""",

    'description': """
        Export Template for KROS system
    """,

    'author': "Smartteksas",
    'website': "https://www.smartteksas.com",

    'category': 'Tools',
    'version': '0.2',

    'depends': [
        'account',
        'sk_invoice',
    ],

    'data': [
        'views/account_move_views.xml',
        'views/res_partner_bank_views.xml',
        'report/account_move_templates.xml',
    ],
}
