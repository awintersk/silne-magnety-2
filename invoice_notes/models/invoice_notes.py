# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

MESSAGE_1 = _("Supply of goods is exempt. Supply of services - VAT reverse charge.")
MESSAGE_2 = _("Delivery according to §47 of VAT act – VAT exempt export of goods and services to third country")


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_message = fields.Char(compute='_get_inv_message', store=False)

    def _get_inv_message(self):
        for i in self:
            eu_country_group = self.env['res.country.group'].browse(int(
                self.env['ir.config_parameter'].get_param('account.inv_eu_country_group')))
            non_eu_country_group = self.env['res.country.group'].browse(int(
                self.env['ir.config_parameter'].get_param('account.inv_no_eu_country_group')))

            if i.partner_id.country_id:
                # VAT registered company from EU with delivery in other country than Slovakia - MESSAGE_1
                if i.partner_id.country_id.id in eu_country_group.country_ids.ids and \
                        i.partner_shipping_id.country_id.with_context(lang='en_US').name != 'Slovakia':
                    i.invoice_message = MESSAGE_1

                # Customer is outside EU (no matter if B2C or B2B and if VAT registered or not, this is for all the
                # same), VAT is 0%
                elif i.partner_id.country_id.id in non_eu_country_group.country_ids.ids:
                    i.invoice_message = MESSAGE_2

                else:
                    i.invoice_message = False
            else:
                i.invoice_message = False
