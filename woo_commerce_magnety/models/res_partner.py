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

METADATA_FIELDS = {
    'billing_company_wi_tax': 'vat',
}


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _woo_search_create_company(self, customer_vals):
        company_name = customer_vals.get('company')
        if not company_name:
            return False

        partner = self.env['res.partner'].search([
            ('name', '=', company_name),
            ('is_company', '=', True),
        ])
        if partner:
            return partner

        state_code = customer_vals.get('state', False)
        country_code = customer_vals.get('country', False)
        country = self.get_country(country_code)
        state = self.create_or_update_state_ept(country_code, state_code, False, country)

        company_vals = {
            'name': company_name,
            'is_company': True,
            'is_woo_customer': True,
            'email': customer_vals.get("email", False),
            'phone': customer_vals.get('phone', False),
            'street': customer_vals.get('address_1', False),
            'street2': customer_vals.get('address_2', False),
            'city': customer_vals.get('city', False),
            'zip': customer_vals.get('postcode', False),
            'state_id': state and state.id,
            'country_id': country and country.id,
        }
        return self.env['res.partner'].create(company_vals)

    def woo_create_or_update_customer(self, customer_val, instance, parent_id, partner_type, customer_id=False, meta_data={}):
        def get_meta_line(meta, key):
            for line in meta:
                if line.get('key') == key:
                    return line.get('value')
            return False

        address_key_list = ['name', 'street', 'street2', 'city', 'zip', 'phone', 'state_id', 'country_id', 'vat']

        first_name = customer_val.get("first_name")
        last_name = customer_val.get("last_name")
        if not first_name and not last_name:
            return False
        company_name = customer_val.get("company")

        # Get meta_data vals
        meta_data_vals = {}
        for key, field in METADATA_FIELDS.items():
            meta_data_vals[field] = get_meta_line(meta_data, key)

        partner_vals = self.woo_prepare_partner_vals(customer_val, instance, meta_data_vals)
        woo_partner_values = {'woo_customer_id': customer_id, 'woo_instance_id': instance.id}

        if partner_type == 'delivery':
            address_key_list.remove("phone")
        if company_name:
            address_key_list.append('company_name')
            partner_vals.update({'company_name': company_name})

        address_partner = self.woo_search_address_partner(partner_vals, address_key_list, parent_id, partner_type)
        if address_partner:

            if not parent_id and customer_id and not address_partner.is_woo_customer:
                address_partner.create_woo_res_partner_ept(woo_partner_values)
                address_partner.write({'is_woo_customer': True})
            return address_partner

        if 'company_name' in partner_vals:
            partner_vals.pop('company_name')
        if parent_id:
            partner_vals.update({'parent_id': parent_id.id})
        partner_vals.update({'type': partner_type})
        address_partner = self.with_context(no_vat_validation=True).create(partner_vals)
        if not parent_id and customer_id:
            address_partner.create_woo_res_partner_ept(woo_partner_values)
            address_partner.write({'is_woo_customer': True})
        company_name and address_partner.write({'company_name': company_name})
        return address_partner

    def woo_prepare_partner_vals(self, vals, instance, meta_data_vals={}):
        email = vals.get("email", False)
        first_name = vals.get("first_name")
        last_name = vals.get("last_name")
        name = "%s %s" % (first_name, last_name)
        phone = vals.get("phone")
        address1 = vals.get("address_1")
        address2 = vals.get("address_2")
        city = vals.get("city")
        zipcode = vals.get("postcode")
        state_code = vals.get("state")
        country_code = vals.get("country")

        country = self.get_country(country_code)
        state = self.create_or_update_state_ept(country_code, state_code, False, country)

        partner_vals = {
            'email': email or False, 'name': name, 'phone': phone,
            'street': address1, 'street2': address2, 'city': city, 'zip': zipcode,
            'state_id': state and state.id or False, 'country_id': country and country.id or False,
            'is_company': False, 'lang': instance.woo_lang_id.code, **meta_data_vals,
        }
        update_partner_vals = self.remove_special_chars_from_partner_vals(partner_vals)
        return update_partner_vals

