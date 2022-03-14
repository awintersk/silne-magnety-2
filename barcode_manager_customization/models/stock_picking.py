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

from odoo import models, fields, _

_logger = getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

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


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def split_move_line_for_order(self, qty, order_int_id, package_int_id=None, package_type_int_id=None):
        """
        Used for barcode customization
        :type qty float
        :type order_int_id int
        :type package_int_id int
        :type package_type_int_id int
        :rtype: dict
        """
        new_move_ids = None
        location_env = self.env['stock.location']
        picking_env = self.env['stock.picking']
        package_env = self.env['stock.quant.package']

        location_id = location_env.search([('barcode', '=', 'WH-OUTPUT')])

        if not location_id:
            _logger.warning(location_id)
            return {}

        order_picking_id = picking_env.search([
            ('sale_id', '=', order_int_id),
            ('location_dest_id', '=', location_id.id),
            ('state', 'in', ('waiting', 'confirmed', 'assigned'))
        ], limit=1)

        if not order_picking_id:
            _logger.warning(order_picking_id)
            return {}

        normalized_qty = self.product_uom_id._compute_quantity(qty, self.product_uom_id, rounding_method='HALF_UP')

        new_picking_id = self.picking_id.copy({
            'name': '/',
            'move_lines': [],
            'move_line_ids': [],
            'purchase_id': self.picking_id.purchase_id.id
        })

        if package_int_id is None:
            package_id = package_env
        elif package_int_id > 0:
            package_id = package_env.browse(package_int_id)
        elif package_int_id == 0:
            package_values = {}
            if package_type_int_id:
                package_values['packaging_id'] = package_type_int_id
            package_id = package_env.with_context(picking_id=order_picking_id.id).create(package_values)
        else:
            package_id = package_env

        if self.product_uom_qty == normalized_qty:
            self.move_id.picking_id = new_picking_id.id
            self.write(dict(
                picking_id=new_picking_id.id,
                qty_done=normalized_qty,
            ))
            if package_id:
                self.write({'result_package_id': package_id.id})
        elif self.product_uom_qty > normalized_qty:
            split_move = self.move_id._split(normalized_qty)
            self.product_uom_qty -= normalized_qty

            new_move_ids = self.env['stock.move'].create([{
                **move_data,
                'picking_id': new_picking_id.id,
                'quantity_done': normalized_qty,
            } for move_data in split_move])

            if package_id:
                new_move_ids.move_line_ids.write({'result_package_id': package_id.id})

            new_move_ids._action_confirm(merge=False)
        ctx = self.env.context.copy()

        ctx.update({
            'dest_ids': new_move_ids.move_dest_ids if new_move_ids else self.move_id.move_dest_ids,
            'dest_id': order_picking_id.move_ids_without_package.
                filtered(lambda move: move.product_id.id == self.product_id.id)
        })
        new_picking_id.action_confirm()
        new_picking_id.with_context(ctx).button_validate()

        if package_id:
            response_package = {'id': package_id.id, 'name': package_id.name}
        else:
            response_package = {'id': 0, 'name': _('Without box')}

        response = {
            'confirmed': True,
            'reload': True,
            'orderPickingId': order_picking_id.id,
            'packageId': response_package
        }

        if sum(self.picking_id.move_line_ids.mapped('product_uom_qty')) == 0:
            response['reload'] = False

        return response
