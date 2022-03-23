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

from odoo import fields, models, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    is_gift_product = fields.Boolean(related='product_id.is_gift')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _get_move_line_ids_fields_to_read(self):
        response = super(StockPicking, self)._get_move_line_ids_fields_to_read()
        response.append('is_gift_product')
        return response

    def add_gift_line(self, product: int) -> int:
        order_line_env = self.env['sale.order.line']
        order_id = self.sale_id

        order_line_gift = order_line_env.search_count([
            ('order_id', '=', order_id.id),
            ('product_id.is_gift', '=', True)
        ])

        if not order_line_gift:
            order_line_id = order_line_env.create({
                'product_id': product,
                'order_id': order_id.id
            })
            order_line_id.product_id_change()

            return order_line_id.id

        return 0
