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

import logging

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    is_gift_product = fields.Boolean(related='product_id.is_gift')
    is_lang_warning_product = fields.Boolean(related='product_id.is_lang_warning')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    picking_sequence_code = fields.Char(related='picking_type_id.sequence_code')

    @api.model
    def _get_move_line_ids_fields_to_read(self):
        response = super(StockPicking, self)._get_move_line_ids_fields_to_read()
        response.extend(['is_gift_product', 'is_lang_warning_product'])
        return response

    def _add_special_product(self, product, field):
        """
        :param int product:
        :param str field:
        :return: int
        """
        special_fields = ('is_gift', 'is_lang_warning')

        if field not in special_fields:
            raise ValidationError(_('Option is not valid. Option: %s') % field)

        order_line_env = self.env['sale.order.line']
        product_env = self.env['product.product']
        order_id = self.sale_id
        exists_domain = [('order_id', '=', order_id.id)]

        if not product_env.browse(product).qty_available:
            raise UserError(_('Product has zero available qty'))

        if field == 'is_gift':
            exists_domain.append(('product_id.is_gift', '=', True))
        elif field == 'is_lang_warning':
            exists_domain.append(('product_id.is_lang_warning', '=', True))

        order_line_exists = order_line_env.search_count(exists_domain)

        if not order_line_exists:
            order_line_id = order_line_env.create({
                'product_id': product,
                'order_id': order_id.id
            })
            order_line_id.product_id_change()

            return order_line_id.id

        return 0

    def add_gift_line(self, product: int) -> int:
        return self._add_special_product(product, 'is_gift')

    def add_product_warning_line(self, product: int) -> int:
        return self._add_special_product(product, 'is_lang_warning')

    def _get_picking_fields_to_read(self):
        response = super(StockPicking, self)._get_picking_fields_to_read()
        response.extend(['picking_sequence_code'])
        return response
