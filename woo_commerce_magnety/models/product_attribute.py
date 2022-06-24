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


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    woo_attribute_line_ids = fields.One2many(
        'woo.product.attribute.ept',
        'attribute_id',
        string='Woo Attribute Lines',
    )

    def get_attribute_by_slug(self, attribute_dict, attribute_type='radio', create_variant='always',
                              auto_create=False):
        attribute = self.env['woo.product.attribute.ept'].search([
            ('slug', '=', attribute_dict['slug']),
        ], limit=1).attribute_id
        if not attribute and auto_create:
            attribute = self.create({
                'name': attribute_dict['name'],
                'create_variant': create_variant,
                'display_type': attribute_type,
            })
        return attribute


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    woo_attribute_value_ids = fields.One2many(
        'woo.product.attribute.term.ept',
        'attribute_value_id',
        string='Woo Attribute Lines',
    )

    def get_attribute_values_by_slug(self, attribute_term_dict, attribute_id, auto_create=False):
        attribute = self.env['woo.product.attribute.term.ept'].search([
            ('slug', '=', attribute_term_dict['slug']),
            ('attribute_id', '=', attribute_id),
        ], limit=1).attribute_value_id

        if not attribute:
            attribute = self.env['woo.product.attribute.term.ept'].search([
                ('name', '=', attribute_term_dict['name']),
                ('slug', '=', False),
                ('attribute_id', '=', attribute_id),
            ], limit=1).attribute_value_id

        if not attribute:
            attribute = self.search([
                ('name', '=', attribute_term_dict['name']),
                ('attribute_id', '=', attribute_id)
            ], limit=1)

        if not attribute and auto_create:
            return self.create({
                'name': attribute_term_dict['name'],
                'attribute_id': attribute_id,
            })

        return attribute
