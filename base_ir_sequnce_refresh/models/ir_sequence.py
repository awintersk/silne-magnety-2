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

import pytz
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import date_utils


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    refresh_rate = fields.Selection(
        selection=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
    )
    last_refresh_date = fields.Date(
        string='Last Refresh Date',
        default=fields.Date.today,
    )

    def _get_prefix_suffix(self, date=None, date_range=None):

        def _get_lyd(date):
            return date.strftime('%y')[-1]

        def _interpolate(s, d):
            return (s % d) if s else ''

        def _interpolation_dict():
            now = range_date = effective_date = datetime.now(pytz.timezone(self._context.get('tz') or 'UTC'))
            if date or self._context.get('ir_sequence_date'):
                effective_date = fields.Datetime.from_string(date or self._context.get('ir_sequence_date'))
            if date_range or self._context.get('ir_sequence_date_range'):
                range_date = fields.Datetime.from_string(date_range or self._context.get('ir_sequence_date_range'))

            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
            }
            res = {}
            for key, format in sequences.items():
                res[key] = effective_date.strftime(format)
                res['range_' + key] = range_date.strftime(format)
                res['current_' + key] = now.strftime(format)

            custom_sequences = {'yld': _get_lyd}
            for key, format in custom_sequences.items():
                res[key] = format(effective_date)
                res['range_' + key] = format(range_date)
                res['current_' + key] = format(now)

            return res

        try:
            interpolated_prefix, interpolated_suffix = super()._get_prefix_suffix(date=date, date_range=date_range)
        except Exception as e:
            self.ensure_one()
            d = _interpolation_dict()
            try:
                interpolated_prefix = _interpolate(self.prefix, d)
                interpolated_suffix = _interpolate(self.suffix, d)
            except ValueError:
                raise UserError(_('Invalid prefix or suffix for sequence \'%s\'') % self.name)

        return interpolated_prefix, interpolated_suffix

    def _refresh(self):
        for sequence in self:
            sequence.number_next_actual = 1
            sequence.last_refresh_date = fields.Date.today()

    def cron_refresh_sequence(self):
        today = fields.Date.today()
        week_ago = date_utils.subtract(today, days=7)
        month_ago = date_utils.subtract(today, months=1)
        year_ago = date_utils.subtract(today, years=1)

        self.search([
            '|', '&', ('refresh_rate', '=', 'daily'),
                        ('last_refresh_date', '<', today),
            '|', '&', ('refresh_rate', '=', 'weekly'),
                        ('last_refresh_date', '<', week_ago),
            '|', '&', ('refresh_rate', '=', 'monthly'),
                        ('last_refresh_date', '<', month_ago),
                 '&', ('refresh_rate', '=', 'yearly'),
                        ('last_refresh_date', '<', year_ago),
        ])._refresh()
