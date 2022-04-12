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

from typing import List, Union
from logging import getLogger

from odoo import models, fields, _, api

_logger = getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    picking_sequence_code = fields.Char(related='picking_type_id.sequence_code')

    def get_barcode_view_state(self):
        product_env = self.env['product.product']
        response_list = super().get_barcode_view_state()

        for response in response_list:
            picking_id = self.browse(response['id'])
            response['barcode_sale_order_ids'] = picking_id.barcode_sale_order_ids.read(['id'])
            for line in filter(lambda el: el.get('product_id'), response['move_line_ids']):
                product_id = product_env.browse(line['product_id']['id'])

        return response_list

    barcode_sale_order_ids = fields.One2many(
        comodel_name='sale.order',
        compute='_compute_barcode_sale_order_ids'
    )

    def _compute_barcode_sale_order_ids(self):
        for rec in self:
            rec.barcode_sale_order_ids = rec.purchase_id._get_sale_orders()

    def _put_in_pack(self, move_line_ids, create_package_level=True):
        self.env.context = dict(self._context, picking_id=self.id)
        return super(StockPicking, self)._put_in_pack(move_line_ids, create_package_level)

    def get_stock_package_json(self, package_type='pallet'):
        return self.env['stock.quant.package'].search_read(
            domain=[('packaging_id.packing_type', '=', package_type)],
            fields=['name'],
            order='id desc'
        )

    def put_in_pack_line(self, move_line_int_ids: List[int]) -> Union[int, bool]:
        """Needed for barcode view. Put current lines into new package"""
        move_line_ids = self.env['stock.move.line'].browse(move_line_int_ids)
        for line_id in move_line_ids:
            line_id.write({'qty_done': line_id.product_uom_qty})
        package_id = self._put_in_pack(move_line_ids)
        return package_id.id if package_id else False

    def create_backorder(self):
        """Needed for Rpc"""
        self.move_line_ids.write({'qty_done': 0})
        self._create_backorder()
        return True

    def _action_done(self):
        response = super(StockPicking, self)._action_done()
        self.env['stock.quant']._quant_tasks()
        return response

    @api.model
    def _get_move_line_ids_fields_to_read(self):
        response = super(StockPicking, self)._get_move_line_ids_fields_to_read()
        return [*response, 'product_weight']

    def _get_picking_fields_to_read(self):
        response = super(StockPicking, self)._get_picking_fields_to_read()
        if 'picking_sequence_code' not in response:
            response.append('picking_sequence_code')
        return response
