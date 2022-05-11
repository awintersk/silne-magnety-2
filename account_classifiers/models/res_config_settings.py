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


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    woo_invoice_classifer_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Invoice Classifier Sequence',
    )
    woo_reversal_classifer_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Credit Note Classifier Sequence',
    )

    @api.onchange('woo_instance_id')
    def onchange_woo_instance_id(self):
        """
        This method is to set data in Woocommerce configuration base in onchange of instance.
        """
        res = super().onchange_woo_instance_id()
        instance = self.woo_instance_id or False
        if not instance:
            return res
        self.woo_invoice_classifer_sequence_id = instance.invoice_classifer_sequence_id.id
        self.woo_reversal_classifer_sequence_id = instance.reversal_classifer_sequence_id.id
        return res

    def execute(self):
        """
        This method is used to set the configured values in the Instance.
        """
        res = super(ResConfigSettings, self).execute()
        instance = self.woo_instance_id

        if not instance:
            return res

        instance_values = {
            'invoice_classifer_sequence_id': self.woo_invoice_classifer_sequence_id.id,
            'reversal_classifer_sequence_id': self.woo_reversal_classifer_sequence_id.id,
        }
        instance.write(instance_values)

        return res

