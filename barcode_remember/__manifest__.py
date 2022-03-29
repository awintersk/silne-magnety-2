# -*- coding: UTF-8 -*-
################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2019 SmartTek (<https://smartteksas.com/>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

{
    'name': "Barcode Remember",

    'summary': """
    """,

    'description': """
    """,

    'author': "SmartTek",
    'website': "https://smartteksas.com",

    'category': 'Purchases',
    'version': '14.0.0.2',

    'depends': [
        'base',
        'product',
        'sale',
        'stock_barcode',
    ],

    'demo': [
        'data/product_template_demo.xml',
    ],

    'data': [
        # 'security/ir.model.access.csv',
        'views/assets_views.xml',
        'views/product_template_views.xml',
    ],

    'qweb': [
        'static/src/xml/remember.xml'
    ]
}
