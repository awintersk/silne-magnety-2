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


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    status = fields.Selection(
        selection=[
            ('rfq_sent', 'Odoslaná žiadosť o cenovú ponuku'),
            ('ordered', 'Objednané'),
            ('made', 'Vyrobené'),
            ('ordered_transport', 'Objednaná preprava'),
            ('in_transit', 'V preprave'),
            ('docs_sent', 'Odoslané dokumenty na preclenie'),
            ('done', 'Dodané'),
        ],
        string='Picking status',
        default='rfq_sent',
        compute='_compute_status',
        store=True,
        readonly=False,
    )
    partner_id = fields.Many2one(
        states={
            'done': [('readonly', True)],
            'cancel': [('readonly', True)],
        },
    )

    @api.depends('state')
    def _compute_status(self):
        for r in self:
            if r.state == 'sent':
                r.status = 'rfq_sent'
            elif r.state == 'purchase':
                r.status = 'ordered'
            elif r.state == 'done':
                r.status = 'done'
            elif r.state == 'cancel':
                r.status = False
            else:
                r.state = r.state

    def write(self, vals):
        res = super().write(vals)
        if 'partner_id' in vals:
            self.picking_ids.filtered(
                lambda r: r.state not in ('done', 'cancel')
            ).partner_id = vals['partner_id']
        return res
