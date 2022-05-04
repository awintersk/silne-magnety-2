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
from odoo.osv import expression

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
        for picking_id in self:
            product_ids = picking_id.move_line_ids.product_id
            move_ids = self.env['stock.move'].search([
                ('product_id', 'in', product_ids.ids),
                ('picking_type_id.sequence_code', '=', 'PICK'),
                ('state', 'in', ('waiting', 'confirmed', 'partially_available'))
            ]).filtered(
                lambda move_id: move_id.reserved_availability < move_id.product_uom_qty
            )
            picking_id.barcode_sale_order_ids = self.env['sale.order'].search([
                ('order_line.product_id', 'in', product_ids.ids),
                ('picking_ids.move_lines', 'in', move_ids.ids)
            ])

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

    def stock_location_for_order_receipt(self, order_int_id):
        """
        :param int order_int_id: Sale Order int id
        :rtype: list[dict[str, Any]]
        :return: Location list
        """
        self.ensure_one()

        sale_picking_ids = self.env['stock.picking'].search([
            ('sale_id', '=', order_int_id),
            ('picking_type_id.sequence_code', '=', 'PICK'),
            ('state', 'not in', ('draft', 'cancel')),
        ])

        domain = [('id', 'child_of', self.location_dest_id.ids)]

        if sale_picking_ids:
            domain = expression.OR([
                domain,
                [('id', 'child_of', sale_picking_ids.location_id.ids), ('usage', '!=', 'view')]
            ])

        location_ids = self.env['stock.location'].search_read(
            domain=domain,
            fields=['id', 'display_name', 'barcode'],
        )
        return location_ids
