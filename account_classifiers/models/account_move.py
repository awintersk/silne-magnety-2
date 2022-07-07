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

import re

from odoo import _, api, fields, models

sequence_ref_pattern = re.compile(r'\d+$')


class AccountMove(models.Model):
    _inherit = 'account.move'

    kros_classifier = fields.Char(
        string='Classifier',
        copy=False,
    )

    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        res = super()._compute_name()

        for move in self.filtered(lambda m: m.name != '/' and m.kros_classifier):
            move.name = move.kros_classifier

        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            ref = False
            if vals.get('move_type') == 'out_invoice':
                if 'invoice_origin' not in vals:
                    continue
                ref = sequence_ref_pattern.findall(vals['invoice_origin'])
                vals['payment_reference'] = ref and ref[0] or vals.get('payment_reference', False)
        return super().create(vals_list)

    def _recompute_payment_terms_lines(self):
        res = super()._recompute_payment_terms_lines()
        if self.move_type == 'out_refund' and self.kros_classifier:
            ref = sequence_ref_pattern.findall(self.kros_classifier)
            if ref:
                self.payment_reference = ref[0]
        return res

    def _get_last_sequence_domain(self, relaxed=False):
        """Get the sql domain to retreive the previous sequence number.
        :param relaxed: see _get_last_sequence.

        :returns: tuple(where_string, where_params): with
            where_string: the entire SQL WHERE clause as a string.
            where_params: a dictionary containing the parameters to substitute
                at the execution of the query.
        """
        where_string, param = super()._get_last_sequence_domain(relaxed)
        where_string += " AND kros_classifier IS NULL"
        return where_string, param
