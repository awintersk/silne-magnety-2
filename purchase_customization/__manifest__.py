################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2021 SmartTek (<https://smartteksas.com>).
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
    'name': "Purchase Customization",
    'version': '14.0.1.1.1',
    'category': 'Inventory/Purchase',
    'author': 'Smart Tek Solutions and Services',
    'website': "https://smartteksas.com/",
    'depends': [
        'purchase',
        'purchase_stock',
        'woo_commerce_ept',
    ],
    'data': [
        'data/ir_exports.xml',
        'views/assets.xml',
        'views/product_supplierinfo_views.xml',
        'views/product_template_views.xml',
        'views/purchase_order_views.xml',
        'report/purchase_order_report_templates.xml',
        'report/purchase_order_report.xml',
    ],
    'license': "AGPL-3",
    'installable': True,
    'application': False,
}
