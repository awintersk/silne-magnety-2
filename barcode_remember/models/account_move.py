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

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, values):
        if values.get('invoice_line_ids'):
            self._exclude_gift_from_invoice_line(values)
            if not values['invoice_line_ids']:
                raise ValidationError(_('Invoice contains only gift product'))
        return super(AccountMove, self).create(values)

    def _exclude_gift_from_invoice_line(self, values: dict) -> dict:
        product_env = self.env['product.product']
        values['invoice_line_ids'] = [
            line for line in values['invoice_line_ids']
            if not product_env.browse(line[2]['product_id']).is_gift
        ]
        return values
