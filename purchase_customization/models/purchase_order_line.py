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


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    hs_code = fields.Char(related='product_id.hs_code')
    hs_description = fields.Text(related='product_id.hs_description')
    net_weight = fields.Float(string='Net Weight', compute='_compute_net_weight', store=True)
    net_weight_uom_name = fields.Char(string='Net Weight UOM', related='product_id.weight_uom_name')

    @api.depends('product_qty', 'product_id.weight')
    def _compute_net_weight(self):
        for line in self:
            line.net_weight = line.product_qty * line.product_id.weight
