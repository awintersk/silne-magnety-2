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

from . import models
from . import excel_tools
from . import wizard

from odoo import SUPERUSER_ID
from odoo.api import Environment


def _post_init(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})

    package_ids = env['stock.quant.package'].search([
        ('quant_ids', '!=', False),
    ], order='create_date desc', limit=1000)

    package_ids.update_order_data()

    for package_id in package_ids:
        if package_id.packaging_id.packing_type != 'pallet':
            continue
        package_id.document_ids = env['documents.document'].search([
            ('name', '=like', f'%%{package_id.name}%%'),
            ('name', '=like', 'Package Currier%%'),
            ('res_model', '=', 'stock.quant.package')
        ])
