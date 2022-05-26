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
from typing import Dict, Any
from odoo import models

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @staticmethod
    def _get_label_report_action(line, report_id):
        """
        :param Dict[str, Any] line:
        :param models.BaseModel report_id:
        :return: Report action
        :rtype: Dict[str, Any]
        """
        report_data = report_id.read([
            'type', 'report_name', 'report_type', 'report_file', 'model'
        ])[0]
        report_data.update({
            'context': {
                'active_ids': [line['product_id']] * abs(line['qty'])
            }
        })
        return report_data

    def actions_print_label_zpl(self, line):
        """
        :param Dict[str, Any] line:
        :return: Report action
        :rtype: Dict[str, Any]
        """
        label_template_env = self.env['zpl.label.template']
        product_env = self.env['product.product']

        product_id = product_env.browse(line['product_id'])

        label_template_id = label_template_env.search([
            ('product_category_ids', 'in', product_id.categ_id.ids)
        ], limit=1)

        if label_template_id:
            return self._get_label_report_action(line, label_template_id.report_id)

        report_id = self.env.ref('stock.label_product_product')
        return self._get_label_report_action(line, report_id)
