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
import re

from odoo import models, _, fields

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    categ_ids = fields.Many2many(
        'product.category', string='Product Categories',
        help="Select category for the current product")

    woo_description = fields.Html("Description", translate=True)
    woo_short_description = fields.Html("Short Description", translate=True)

    def _pull_product_weight_from_attribute(self):
        self.ensure_one()

        get_param = self.env['ir.config_parameter'].get_param
        weight_name_items = get_param('woo_commerce_magnety.product_weight_attribute_name')
        attribute_value_id = None
        value_ids = self.attribute_line_ids.value_ids
        
        for name in weight_name_items.split(','):
            attribute_value_id = self.env['product.attribute.value'].search([
                ('id', 'in', value_ids.ids),
                ('attribute_id.name', '=', name.strip()),
            ], limit=1)
            if attribute_value_id:
                break

        if not attribute_value_id:
            return False

        weight_group = re.match(r'([\d.,]+)\s*(\w+)?', attribute_value_id.name)

        if not weight_group:
            return False

        weight, measure = weight_group.groups()

        if weight.count(','):
            weight = weight.replace(',', '.')

        try:
            weight = float(weight)
        except ValueError:
            msg = _('Can not possible to parse the weight of the product "%s"')
            _logger.warning(msg % self.name)
            return False

        if not measure:
            measure = 'kg'

        measure_map = self.product_attribute_weight_measure_map()
        self.write({
            'weight': weight / measure_map.get(measure.lower(), 1)
        })

        return True

    @staticmethod
    def product_attribute_weight_measure_map():
        return {
            'kg': 1,
            'g': 1000,
            'mg': 1_000_000
        }
