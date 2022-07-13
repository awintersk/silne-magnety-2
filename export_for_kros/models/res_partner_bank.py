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


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    use_in_kros = fields.Boolean(string='Use in Kros')

    @api.constrains('use_in_kros', 'currency_id')
    def _check_use_in_kros(self):
        for r in self.filtered(lambda r: r.use_in_kros):
            if self.env['res.partner.bank'].search_count([
                ('id', '!=', r.id),
                ('use_in_kros', '=', True),
                ('currency_id', '=', r.currency_id.id),
            ]):
                raise models.ValidationError(_('Bank Account used in KROS must be unique per currency.'))
