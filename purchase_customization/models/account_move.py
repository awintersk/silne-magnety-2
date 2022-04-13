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

from math import ceil


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'invoice_line_ids.sale_line_ids.order_id.payment_gateway_id.rounding')
    def _compute_amount(self):
        def round_to_base(x, base):
            return base * ceil(x / base)

        super()._compute_amount()
        for move in self.filtered(
        	lambda r: r.invoice_line_ids.sale_line_ids.order_id.payment_gateway_id.mapped('rounding')
        ):
            base = move.invoice_line_ids.sale_line_ids.order_id.payment_gateway_id[:1].rounding
            if not base:
                continue
            move.update({
                'amount_untaxed': round_to_base(move.amount_untaxed, base),
                'amount_tax': round_to_base(move.amount_tax, base),
                'amount_total': round_to_base(move.amount_total, base),
                'amount_residual': round_to_base(move.amount_residual, base),
                'amount_untaxed_signed': round_to_base(move.amount_untaxed_signed, base),
                'amount_tax_signed': round_to_base(move.amount_tax_signed, base),
                'amount_total_signed': round_to_base(move.amount_total_signed, base),
                'amount_residual_signed': round_to_base(move.amount_residual_signed, base),
            })
