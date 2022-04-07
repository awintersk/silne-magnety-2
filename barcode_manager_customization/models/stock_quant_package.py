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


from odoo import fields, models, _, api


class ProductPackaging(models.Model):
    _inherit = 'product.packaging'

    weight = fields.Float(default=0, help='Package weight without products')


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    def _default_name(self):
        next_by_code = self.env['ir.sequence'].next_by_code
        picking_id = self._picking_id_from_context

        if not picking_id:
            return next_by_code('stock.quant.package') or _('Unknown Pack')

        picking_type_code = picking_id.picking_type_code

        if picking_id.sale_id and picking_type_code == 'internal':
            response = picking_id.sale_id.next_package_name()
        elif picking_type_code == 'incoming':
            response = picking_id.purchase_id.next_package_name()
        else:
            response = next_by_code('stock.quant.package.pallet')

        return response or next_by_code('stock.quant.package') or _('Unknown Pack')

    def default_get(self, fields_list):
        response = super(StockQuantPackage, self).default_get(fields_list)
        packaging_env = self.env['product.packaging']
        picking_id = self._picking_id_from_context

        if 'packaging_id' not in response and picking_id:
            picking_type_code = picking_id.picking_type_code

            if picking_type_code in ('incoming', 'internal'):
                packaging_id = packaging_env.search([('packing_type', '=', 'box')], limit=1)
            elif picking_type_code in ('outgoing',):
                packaging_id = packaging_env.search([('packing_type', '=', 'pallet')], limit=1)
            else:
                packaging_id = False

            if packaging_id:
                response.update(packaging_id=packaging_id.id)

        return response

    name = fields.Char(default=lambda self: self._default_name())
    weight = fields.Float(compute='_compute_weight')
    packaging_weight = fields.Float(
        related='packaging_id.weight',
        string='Packaging Weight',
    )

    @property
    def _picking_id_from_context(self):
        return self.env['stock.picking'].browse(self._context.get('picking_id', 0)).exists()

    @api.depends('packaging_id.weight', 'quant_ids')
    def _compute_weight(self):
        super(StockQuantPackage, self)._compute_weight()
        for rec_id in self:
            if rec_id.packaging_id:
                rec_id.weight = rec_id.weight + rec_id.packaging_id.weight
