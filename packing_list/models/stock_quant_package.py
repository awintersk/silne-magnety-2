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

from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    document_ids = fields.Many2many('documents.document')
    document_count = fields.Integer(compute='_compute_document_count')
    sale_ids = fields.Many2many(
        comodel_name='sale.order',
        compute='_compute_sale_ids',
        store=True,
    )
    packaging_type = fields.Selection(
        related='packaging_id.packing_type',
        store=True,
    )
    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        compute='_compute_carrier_id',
        store=True,
    )

    # --------- #
    #  Compute  #
    # --------- #

    @api.depends('document_ids')
    def _compute_document_count(self):
        for pack_id in self:
            pack_id.document_count = len(pack_id.document_ids)

    @api.depends('quant_ids.quantity', 'quant_ids.location_id')
    def _compute_sale_ids(self):
        sale_order_env = self.env['sale.order']
        picking_int_ids = self._context.get('button_validate_picking_ids', [])
        for pack_id in self:
            order_domain = [('picking_ids.state', '!=', 'cancel')]
            if picking_int_ids:
                order_domain += [('picking_ids', 'in', picking_int_ids)]
            else:
                order_domain += [('picking_ids.move_line_ids.result_package_id', '=', pack_id.id)]
            pack_id.sale_ids = sale_order_env.search(order_domain)

    @api.depends('quant_ids.location_id', 'sale_ids')
    def _compute_carrier_id(self):
        picking_env = self.env['stock.picking']
        for pack_id in self:
            carrier_id = picking_env.search([
                ('sale_id', 'in', pack_id.sale_ids.ids),
                ('state', '!=', 'cancel'),
            ]).carrier_id
            pack_id.carrier_id = carrier_id[0] if carrier_id else False

    # --------- #
    #  Actions  #
    # --------- #

    def action_documents(self) -> dict:
        action_name = _('Documents')
        self_name = ','.join(self.mapped('name'))
        return {
            'name': f"{action_name} ({self_name})",
            'domain': [('id', 'in', self.document_ids.ids)],
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'views': [(False, 'kanban'), (False, 'list')],
            'view_mode': 'kanban,list',
        }

    def action_generate_packing_document(self) -> dict:
        action = self.env['ir.actions.act_window']._for_xml_id('packing_list.packing_list_action')
        return dict(action, context={
            'package_ids': self.ids,
        })

    # -------- #
    #  Public  #
    # -------- #

    def update_order_data(self):
        self._compute_sale_ids()
        self._compute_carrier_id()
