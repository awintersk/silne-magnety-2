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


class AccountMove(models.Model):
    _inherit = 'account.move'

    oss = fields.Boolean(
        string='OSS',
        compute='_compute_oss',
        store=True,
        readonly=False,
    )

    @api.depends(
        'partner_id.is_vat_payer',
        'invoice_line_ids.sale_line_ids.order_id.payment_gateway_id.with_oss',
    )
    def _compute_oss(self):
        self.oss = False
        for r in self.filtered(
            lambda r: r.invoice_line_ids.sale_line_ids.order_id.mapped('payment_gateway_id')
        ):
            payment_gateways = r.invoice_line_ids.sale_line_ids.order_id.payment_gateway_id
            r.oss = all(payment_gateways.mapped('with_oss')) \
                and not r.partner_id.is_vat_payer
