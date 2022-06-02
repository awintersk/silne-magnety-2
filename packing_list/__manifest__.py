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
    'name': "Packing List",

    'summary': """
    """,

    'description': """
    """,

    'author': "SmartTek",
    'website': "https://smartteksas.com",

    'category': 'Inventory/Delivery',
    'version': '14.0.0.11',

    'depends': [
        'base',
        'stock',
        'delivery',
        'documents',
        'report_xlsx',
        'sale_customization',
        'w_open_many2many_tags',
        'barcode_manager_customization',
    ],

    'demo': [
    ],

    'data': [
        'security/ir.model.access.csv',

        'data/documents_folder_data.xml',
        'data/ir_actions_server_data.xml',

        'views/stock_quant_package_views.xml',

        'wizard/packing_list_wizard_views.xml',
    ],

    'qweb': [
    ],

    'post_init_hook': '_post_init'
}
