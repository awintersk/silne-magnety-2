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
from math import ceil, floor


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends(
        'order_line.price_total',
        'payment_gateway_id.rounding_id.rounding',
        'payment_gateway_id.rounding_id.rounding_method',
    )
    def _amount_all(self):
        super()._amount_all()
        for order in self.filtered('payment_gateway_id.rounding_id'):
            rounding = order.payment_gateway_id.rounding_id
            order.update({
                'amount_total': rounding.round(order.amount_total),
            })

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped, final, date)
        # Add cash rounding to invoices from woocommerce gateway
        moves_to_round = moves.filtered(
            lambda r: r.invoice_line_ids.sale_line_ids.order_id.payment_gateway_id.rounding_id
        )
        for move in moves_to_round:
            move.invoice_cash_rounding_id = move.invoice_line_ids. \
                sale_line_ids.order_id.payment_gateway_id.rounding_id[:1]
        return moves
