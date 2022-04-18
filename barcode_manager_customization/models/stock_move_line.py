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

from typing import List, Tuple

from odoo import fields, models, api, _
from odoo.tools import float_compare, float_is_zero, defaultdict, float_round
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Move(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        self.filtered(lambda move: move.state == 'draft')._action_confirm()  # MRP allows scrapping draft moves
        moves = self.exists().filtered(lambda x: x.state not in ('done', 'cancel'))
        moves_todo = self.env['stock.move']

        # Cancel moves where necessary ; we should do it before creating the extra moves because
        # this operation could trigger a merge of moves.
        for move in moves:
            if move.quantity_done <= 0:
                if move.purchase_line_id:
                    no_backorder = move.move_line_ids.filtered(lambda r: r.product_uom_qty != r.qty_done)
                    if not no_backorder:
                        move._action_cancel()
                else:
                    if float_compare(move.product_uom_qty, 0.0,
                                     precision_rounding=move.product_uom.rounding) == 0 or cancel_backorder:
                        move._action_cancel()

        # Create extra moves where necessary
        for move in moves:
            if move.purchase_line_id:
                if move.state == 'cancel':
                    continue
            else:
                if move.state == 'cancel' or move.quantity_done <= 0:
                    continue

            moves_todo |= move._create_extra_move()

        moves_todo._check_company()
        # Split moves where necessary and move quants
        backorder_moves_vals = []
        for move in moves_todo:
            # If B/O is not enabld for this, then skip
            if move.purchase_line_id:
                if not move.move_line_ids.filtered(lambda r: r.product_uom_qty != r.qty_done):
                    continue
            # To know whether we need to create a backorder or not, round to the general product's
            # decimal precision and not the product's UOM.
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(move.quantity_done, move.product_uom_qty, precision_digits=rounding) < 0:
                # Need to do some kind of conversion here
                qty_split = move.product_uom._compute_quantity(move.product_uom_qty - move.quantity_done,
                                                               move.product_id.uom_id, rounding_method='HALF-UP')
                new_move_vals = move._split(qty_split)
                backorder_moves_vals += new_move_vals

        backorder_moves = self.env['stock.move'].create(backorder_moves_vals)
        backorder_moves._action_confirm(merge=False)
        if cancel_backorder:
            backorder_moves.with_context(moves_todo=moves_todo)._action_cancel()
        moves_todo.mapped('move_line_ids').sorted()._action_done()
        # Check the consistency of the result packages; there should be an unique location across
        # the contained quants.
        for result_package in moves_todo \
                .mapped('move_line_ids.result_package_id') \
                .filtered(lambda p: p.quant_ids and len(p.quant_ids) > 1):
            if len(result_package.quant_ids.filtered(
                    lambda q: not float_is_zero(abs(q.quantity) + abs(q.reserved_quantity),
                                                precision_rounding=q.product_uom_id.rounding)).mapped(
                'location_id')) > 1:
                raise UserError(_(
                    'You cannot move the same package content more than once in the same transfer or split the same package into two location.'))
        picking = moves_todo.mapped('picking_id')
        moves_todo.write({'state': 'done', 'date': fields.Datetime.now()})

        move_dests_per_company = defaultdict(lambda: self.env['stock.move'])
        for move_dest in moves_todo.move_dest_ids:
            move_dests_per_company[move_dest.company_id.id] |= move_dest
        for company_id, move_dests in move_dests_per_company.items():
            move_dests.sudo().with_company(company_id)._action_assign()

        # We don't want to create back order for scrap moves
        # Replace by a kwarg in master
        if self.env.context.get('is_scrap'):
            return moves_todo

        if picking and not cancel_backorder:
            picking._create_backorder()
        return moves_todo

    def _action_assign(self):
        if self.env.context.get('dest_ids') and \
                set(self.ids).issubset(self.env.context['dest_ids'].ids):
            return super(Move, self.env.context.get('dest_id'))._action_assign()
        return super(Move, self)._action_assign()

    def _split(self, qty, restrict_partner_id=False):
        """ Overrides the default _split function so as to enabled back order even for moves with zero quantity_done
        """
        self.ensure_one()
        if self.state in ('done', 'cancel'):
            raise UserError('You cannot split a stock move that has been set to \'Done\'.')
        elif self.state == 'draft':
            # we restrict the split of a draft move because if not confirmed yet, it may be replaced by several other moves in
            # case of phantom bom (with mrp module). And we don't want to deal with this complexity by copying the product that will explode.
            raise UserError('You cannot split a draft move. It needs to be confirmed first.')
        # Commented out so as to allow splitting moves with unchanged product_qty
        if not self.purchase_line_id:
            if float_is_zero(qty, precision_rounding=self.product_id.uom_id.rounding) or self.product_qty <= qty:
                return []

        decimal_precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # `qty` passed as argument is the quantity to backorder and is always expressed in the
        # quants UOM. If we're able to convert back and forth this quantity in the move's and the
        # quants UOM, the backordered move can keep the UOM of the move. Else, we'll create is in
        # the UOM of the quants.
        uom_qty = self.product_id.uom_id._compute_quantity(qty, self.product_uom, rounding_method='HALF-UP')
        if float_compare(qty,
                         self.product_uom._compute_quantity(uom_qty, self.product_id.uom_id, rounding_method='HALF-UP'),
                         precision_digits=decimal_precision) == 0:
            defaults = self._prepare_move_split_vals(uom_qty)
        else:
            defaults = self.with_context(force_split_uom_id=self.product_id.uom_id.id)._prepare_move_split_vals(qty)

        if restrict_partner_id:
            defaults['restrict_partner_id'] = restrict_partner_id

        # TDE CLEANME: remove context key + add as parameter
        if self.env.context.get('source_location_id'):
            defaults['location_id'] = self.env.context['source_location_id']
        new_move_vals = self.with_context(rounding_method='HALF-UP').copy_data(defaults)

        # Update the original `product_qty` of the move. Use the general product's decimal
        # precision and not the move's UOM to handle case where the `quantity_done` is not
        # compatible with the move's UOM.
        new_product_qty = self.product_id.uom_id._compute_quantity(self.product_qty - qty, self.product_uom,
                                                                   round=False)
        new_product_qty = float_round(new_product_qty, precision_digits=self.env['decimal.precision'].precision_get(
            'Product Unit of Measure'))
        self.with_context(do_not_unreserve=True, rounding_method='HALF-UP').write({'product_uom_qty': new_product_qty})
        return new_move_vals


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    product_barcode = fields.Char(related='product_id.barcode', readonly=False)
    product_weight = fields.Float(related='product_id.weight')

    def _new_package(self, type_int_id, weight):
        package_values = {}
        if type_int_id > 0:
            package_values['packaging_id'] = type_int_id
        if type(weight) in (float, int):
            package_values['shipping_weight'] = weight
        return self.env['stock.quant.package'].create(package_values)

    def split_and_put_in_pack(self, qty, package_int_id, package_type_int_id=None, weight=None, is_new_package=False):
        """
            Needed for barcode window. Split current line and connect with existing package
            :param float qty:
            :param int package_int_id:
            :param int package_type_int_id:
            :param float weight:
            :param boolean is_new_package:
            :rtype: dict
        """
        self.ensure_one()

        new_package = None
        package_env = self.env['stock.quant.package']

        if is_new_package:
            new_package = self._new_package(package_type_int_id, weight)
            new_package._compute_weight()
            package_int_id = new_package.id
        elif package_int_id > 0 and type(weight) in (float, int):
            package_env.browse(package_int_id).write({'shipping_weight': weight})

        uom_id = self.product_uom_id
        new_qty = uom_id._compute_quantity(self.product_uom_qty - qty, to_unit=uom_id, round=False)

        if new_qty > 0:
            self.copy({
                'product_uom_qty': qty,
                'qty_done': qty,
                'result_package_id': package_int_id,
            })
            self.write({'product_uom_qty': new_qty, 'qty_done': 0})
            self._quant_update_reserved_qty(qty)
        else:
            self.write({'qty_done': qty, 'result_package_id': package_int_id})

        return new_package.read(['name', 'packaging_id', 'weight'])[0] if new_package else None

    @api.model
    def _quant_update_reserved_qty(self, quantity: float) -> List[Tuple]:
        self.ensure_one()
        return self.env['stock.quant']._update_reserved_quantity(
            product_id=self.product_id,
            location_id=self.location_id,
            quantity=quantity,
            lot_id=self.lot_id,
            package_id=self.package_id,
            owner_id=self.owner_id,
            strict=True
        )

    def put_in_exists_pack(self, package_int_id: int, use_qty_done: bool = False) -> bool:
        """Needed for barcode view. Connect current lines with existing package"""
        for rec in self:
            rec.split_and_put_in_pack(rec.qty_done if use_qty_done else rec.product_uom_qty, package_int_id)
        return True

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
