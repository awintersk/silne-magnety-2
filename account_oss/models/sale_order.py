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


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_is_vat_payer = fields.Boolean(string='Partner is VAT Payer')
    partner_is_company = fields.Boolean(string='Partner is company')

    def update_woo_order_vals(self, order_data, woo_order_number, woo_instance,
                              workflow_config, shipping_partner):
        def get_meta_line(meta, key, get_value=True):
            for line in meta:
                if line.get('key') == key:
                    return line.get('value') if get_value else True
            return False
        vals = super().update_woo_order_vals(order_data, woo_order_number,
                                             woo_instance, workflow_config,
                                             shipping_partner)

        partner_is_vat_payer = bool(
            get_meta_line(order_data.get('meta_data', []), '_billing_company_wi_vat_enabled'),
        )
        partner_is_company = bool(
            get_meta_line(order_data.get('meta_data', []), 'billing_company_wi_id', get_value=False),
        )
        vals.update({
            'partner_is_vat_payer': partner_is_vat_payer,
            'partner_is_company': partner_is_company,
        })

        return vals

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        fiscal_position = self.env['account.fiscal.position'] \
            .browse(invoice_vals.get('fiscal_position_id', False))
        invoice_vals.update({
            'oss': fiscal_position.oss
        })
        return invoice_vals
