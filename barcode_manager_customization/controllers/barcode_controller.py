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
        sale_ids = move_line.picking_id.purchase_id._get_sale_orders()
        picking_ids = request.env['stock.picking'].search([
            ('sale_id', 'in', sale_ids.ids),
            ('location_dest_id.barcode', '=', 'WH-OUTPUT'),
        ])
        move_dest_ids = move_line.move_id.move_dest_ids

        response = [
            {
                'id': picking_id.sale_id.id,
                'name': picking_id.sale_id.name,
                'partnerName': picking_id.sale_id.partner_id.name,
                'qtyToDeliver': move_dest_ids.product_uom_qty - move_dest_ids.reserved_availability,
                'qty': 0,
            } for picking_id in picking_ids
        ]

        return list(filter(lambda el: el['qtyToDeliver'], response))
