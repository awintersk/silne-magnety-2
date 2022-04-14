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

from typing import Dict, List, Optional, Tuple
from odoo.http import request, route, Controller


class RememberStockBarcodeController(Controller):

    @route('/barcode_remember/warning/country', type='json', methods=['POST'], auth='user')
    def barcode_warranty_language(self, picking: int):
        picking_id = request.env['stock.picking'].browse(picking)
        if picking_id.sale_id:
            country_id = picking_id.sale_id.partner_id.country_id
            return {
                'country': country_id.read(['name', 'image_url'])[0] if country_id else {},
            }
        else:
            return {'country': {}}

    @route('/barcode_remember/package/weight_data', type='json', methods=['POST'], auth='user')
    def barcode_remember_package_weight_data(self, picking: int) -> List[Optional[Dict]]:
        picking_id = request.env['stock.picking'].browse(picking)
        line_ids = picking_id.move_line_ids

        if not line_ids:
            return []

        field2read = ['shipping_weight', 'name', 'weight_uom_name', 'weight']
        package_ids = line_ids.package_id | line_ids.result_package_id
        package_list = package_ids.read(field2read)

        for package in package_list:
            move_ids = line_ids.filtered(lambda move_id: package['id'] in package_ids.ids)
            package['weight'] += sum(move_ids.product_id.mapped('weight'))

        return package_list

    @route('/barcode_remember/package/weight_set', type='json', methods=['POST'], auth='user')
    def barcode_remember_package_weight_set(self, package_list: List[Tuple[int, float]]) -> bool:
        package_env = request.env['stock.quant.package']
        for package_int_id, weight in package_list:
            package_id = package_env.browse(package_int_id)
            if package_id.exists():
                package_id.write({'shipping_weight': weight})
        return True
