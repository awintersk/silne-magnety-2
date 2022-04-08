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

from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    package_ids = fields.Many2many('stock.quant.package')

    # --------- #
    #  Actions  #
    # --------- #

    def action_generate_packing_document(self) -> dict:
        action = self.env['ir.actions.act_window']._for_xml_id('packing_list.packing_list_action')
        return dict(action, context={
            'sale_ids': self.ids,
        })

    # --------- #
    #  Private  #
    # --------- #

    def _get_delivery_boxes_ids(self):
        return self.picking_ids.filtered(
            lambda rec: rec.location_dest_id.barcode == 'WH-OUTPUT' and rec.state != 'cancel'
        ).mapped(
            lambda rec: rec.move_line_ids.package_id
        )
