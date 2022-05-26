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

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProductLabelMultiPrint(models.TransientModel):
    _inherit = 'product.label.multi.print'

    zpl_preview = fields.Image(compute='_compute_zpl_preview')

    @api.depends('report_id')
    def _compute_zpl_preview(self):
        template_env = self.env['zpl.label.template']

        for label in self:
            report_id = label.report_id

            if not report_id:
                label.zpl_preview = False
                continue

            template_id = template_env.search([('report_id', '=', report_id.id)])

            if not template_id:
                label.zpl_preview = False
                continue

            label.zpl_preview = template_id.zpl_image
