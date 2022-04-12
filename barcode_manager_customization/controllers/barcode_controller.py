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

from odoo.http import route, Controller, request


class BarcodeController(Controller):

    @route('/product_order_dialog_data', type='json', method='POST', auth='user')
    def product_order_dialog_data(self, product_int_id: int, line_id: int):
        move_line = request.env['stock.move.line'].browse(line_id)

        def get_qty2deliver(move) -> float:
            return move.product_uom_qty - move.reserved_availability

        return [
            {
                'id': move_id.picking_id.sale_id.id,
                'name': move_id.picking_id.sale_id.name,
                'partnerName': move_id.picking_id.sale_id.partner_id.name,
                'qtyToDeliver': get_qty2deliver(move_id),
                'qty': 0,
            }
            for move_id in move_line.move_id.move_dest_ids
            if get_qty2deliver(move_id) > 0
        ]
