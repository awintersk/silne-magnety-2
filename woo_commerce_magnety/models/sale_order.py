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


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update({
            'woo_instance_origin_id': self.woo_instance_id.id,
        })
        return invoice_vals

    def woo_order_billing_shipping_partner(self, order_data, woo_instance, queue_line, common_log_book_id):
        partner_obj = self.env['res.partner']
        woo_partner_obj = self.env['woo.res.partner.ept']
        partner = False

        if not order_data.get("billing"):
            message = "- System could not find the billing address in WooCommerce order : %s" % (order_data.get("id"))
            self.create_woo_log_lines(message, common_log_book_id, queue_line)
            return False, False, False

        woo_partner = woo_partner_obj.search([("woo_customer_id", "=", order_data.get('customer_id')),
                                              ("woo_instance_id", "=", woo_instance.id)], limit=1)
        if woo_partner:
            partner = woo_partner.partner_id

        billing_partner = partner_obj.woo_create_or_update_customer(order_data.get("billing"), woo_instance, partner,
                                                                    'invoice', order_data.get('customer_id', False),
                                                                    order_data.get('meta_data', {}))
        if not partner:
            partner = billing_partner
        shipping_partner = partner_obj.woo_create_or_update_customer(order_data.get("shipping"), woo_instance, partner,
                                                                     'delivery')
        if not shipping_partner:
            shipping_partner = partner

        is_company = order_data.get('wi_as_company')
        if not is_company:
            return partner, billing_partner, shipping_partner
        # search/create the company
        company_partner = partner_obj._woo_search_create_company(order_data.get('billing'))
        if company_partner:
            (billing_partner | shipping_partner).parent_id = company_partner
        return partner, billing_partner, shipping_partner

    def create_woo_orders(self, queue_lines, common_log_book_id):
        res = super().create_woo_orders(queue_lines, common_log_book_id)
        for order in res:
            for partner in (order.partner_id | order.partner_invoice_id | order.partner_shipping_id):
                try:
                    partner.with_context(no_vat_validation=False).check_vat()
                except ValidationError:
                    order.activity_schedule('woo_commerce_magnety.mail_act_vat_check',
                        user_id=order.user_id.id,
                        note=_('Please check the VAT number of the customer %s.') % (partner.name))
        return res
