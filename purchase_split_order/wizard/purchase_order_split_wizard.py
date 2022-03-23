################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2019 SmartTek (<https://smartteksas.com>).
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

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OrderSplitWizardLine(models.TransientModel):
    _name = 'purchase.order.split.wizard.line'
    _description = 'Order Split Wizard Line'

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res.update({
            'product_qty': self.order_line_id.product_qty,
            'date_planned': self.order_line_id.date_planned,
        })
        return res

    order_split_wizard_id = fields.Many2one(
        'purchase.order.split.wizard',
        string="Parent Wizard",
        required=True,
    )
    order_line_id = fields.Many2one(
        'purchase.order.line',
        string='Order Line',
        required=True,
    )
    product_id = fields.Many2one(related='order_line_id.product_id')
    product_name = fields.Text(related='order_line_id.name')
    date_planned = fields.Datetime(string='Delivery Date')
    product_qty = fields.Float(string='Quantity')
    uom_id = fields.Many2one(related='order_line_id.product_uom')
    taxes_id = fields.Many2many(related='order_line_id.taxes_id')
    price_unit = fields.Float(related='order_line_id.price_unit')
    price_subtotal = fields.Monetary(related='order_line_id.price_subtotal')
    currency_id = fields.Many2one(related='order_line_id.currency_id')

    to_split = fields.Boolean('Split')

    @api.constrains('product_qty')
    def _check_product_qty(self):
        for r in self:
            if r.product_qty > r.order_line_id.product_qty:
                raise ValidationError(_('Product quantity must be less than quantity of the related line'))


class OrderSplitWizard(models.TransientModel):
    _name = 'purchase.order.split.wizard'
    _description = 'Order Split Wizard'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        res_id = self._context.get('active_id')
        if not res_id:
            return res

        order_id = self.env['purchase.order'].browse(res_id)
        res['order_id'] = order_id.id
        res['order_split_line_ids'] = [
            (0, 0, {
                'order_line_id': order_line.id,
            }) for order_line in order_id.order_line
        ]
        return res

    order_id = fields.Many2one('purchase.order', string='Order', required=True)
    order_split_line_ids = fields.One2many(
        'purchase.order.split.wizard.line',
        'order_split_wizard_id',
        string='Order Split Lines',
    )

    def _action_split(self):
        orders = self.env['purchase.order']
        for r in self:
            lines_to_split = r.order_split_line_ids.filtered('to_split')
            if not lines_to_split:
                continue

            copied_order = r.order_id.copy({'order_line': False})
            lines_full_qty = lines_to_split.filtered(
                lambda line: line.product_qty == line.order_line_id.product_qty)
            lines_full_qty.order_line_id.order_id = copied_order.id,
            for line in lines_full_qty:
                line.order_line_id.date_planned = line.date_planned

            for line in (lines_to_split - lines_full_qty):
                line.order_line_id.copy({
                    'order_id': copied_order.id,
                    'product_qty': line.product_qty,
                    'date_planned': line.date_planned,
                })
                line.order_line_id.product_qty -= line.product_qty
            orders |= copied_order
        return orders

    def button_split(self):
        self.ensure_one()
        order = self._action_split()
        if not order:
            return

        return {
            'name': 'Requests for Quotation',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': order.id,
        }
