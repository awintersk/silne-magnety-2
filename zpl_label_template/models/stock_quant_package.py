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

from logging import getLogger
from typing import Tuple

from odoo import models, api, _

_logger = getLogger(__name__)


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    def get_boxes(self) -> Tuple[dict, dict]:
        move_ids = self.env['stock.move.line'].search([
            ('result_package_id', '=', self.id),
            ('result_package_id.packaging_id.packing_type', '=', 'pallet'),
            ('package_id', '!=', False),
            ('package_id.packaging_id.packing_type', '=', 'box')
        ])

        lines = {}
        total_weight = 0
        total_qty = 0
        total_volume = 0

        for line_id in move_ids:
            package_id = line_id.package_id
            packaging_id = package_id.packaging_id
            name = package_id.name
            line_qty = line_id.qty_done
            volume = packaging_id.width * packaging_id.height * packaging_id.packaging_length
            weight = package_id.shipping_weight

            lines[name] = dict(
                name=name,
                weight=weight,
                qty=lines[name]['qty'] + line_qty if lines.get(name) else line_qty,
                volume=volume
            )

            total_volume += volume
            total_qty += line_qty
            total_weight += weight

        return lines, {
            'weight': total_weight,
            'qty': total_qty,
            'volume': total_volume
        }

    @api.model
    def action_print_via_printnode(self):
        action_name = 'zpl_label_template.package_via_printer_wizard_action'
        action = self.env['ir.actions.act_window']._for_xml_id(action_name)
        return dict(action, context={
            'default_package_ids': self.ids,
        })
