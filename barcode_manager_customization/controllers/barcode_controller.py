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

from typing import List, Dict, Any
from odoo.http import route, Controller, request


class BarcodeController(Controller):

    @route('/product_order_dialog_data', type='json', method='POST', auth='user')
    def product_order_dialog_data(self, line_id: int):
        move_line = request.env['stock.move.line'].browse(line_id)

        return [
            {
                'id': move_id.picking_id.sale_id.id,
                'name': move_id.picking_id.sale_id.name,
                'partnerName': move_id.picking_id.sale_id.partner_id.name,
                'qtyToDeliver': move_id.product_uom_qty - move_id.reserved_availability,
                'qty': 0,
            }
            for move_id in move_line.move_id.move_dest_ids
            if move_id.product_uom_qty - move_id.reserved_availability > 0
        ]

    @route('/barcode/expected/weight', type='json', auth='user')
    def barcode_expected_weight(self, picking_int_id, package_int_id, target_line_int_id, qty):
        """
        :param int picking_int_id:
        :param int package_int_id:
        :param int target_line_int_id:
        :param int qty:
        :rtype: float
        """
        picking_id = request.env['stock.picking'].browse(picking_int_id)
        package_id = request.env['stock.quant.package'].browse(package_int_id)

        expected_weight = package_id.weight
        package_line_int_ids = package_id.move_line_ids.ids

        for line_id in picking_id.move_line_ids:
            line_qty = qty if line_id.id == target_line_int_id else line_id.qty_done
            if line_id.id in package_line_int_ids:
                expected_weight -= line_id.product_weight * (line_id.product_qty - line_qty)
            else:
                expected_weight += line_id.product_weight * line_qty
        return expected_weight
