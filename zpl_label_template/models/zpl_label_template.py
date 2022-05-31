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

import requests
import base64
import logging
import re

from werkzeug.urls import url_join
from requests.exceptions import HTTPError
from uuid import uuid4
from string import punctuation

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ZPLLabelTemplate(models.Model):
    _name = 'zpl.label.template'
    _description = 'ZPL Label Template'

    def _report_default_value(self):
        return self.env.ref('zpl_label_template.default_report_value')._render({
            'name': uuid4().hex
        })

    def _model_id_domain(self):
        return [
            '&',
            ('transient', '=', False),
            '|',
            ('model', '=like', 'sale.%'),
            '|',
            ('model', '=like', 'product.%'),
            '|',
            ('model', '=like', 'stock.%'),
            ('model', '=like', 'purchase.%')
        ]

    name = fields.Char(related='report_id.name', required=True, readonly=False, copy=True)
    model_id = fields.Many2one('ir.model', required=True, ondelete='cascade', domain=_model_id_domain)
    zpl_code = fields.Text(
        related='report_view_id.arch_base',
        readonly=False,
        required=True,
        copy=True,
    )
    active = fields.Boolean(default=True)
    published = fields.Boolean(compute='_compute_published', store=True)
    report_id = fields.Many2one('ir.actions.report', copy=False)
    report_view_id = fields.Many2one('ir.ui.view', copy=False)
    record_int_id = fields.Integer('Record')
    product_category_ids = fields.One2many('product.category', 'zpl_template_id')

    zpl_image = fields.Image(max_width=576, max_height=576)
    dpmm = fields.Selection([
        ('6dpmm', '6 dpmm (152 dpi)'),
        ('8dpmm', '8 dpmm (203 dpi)'),
        ('12dpmm', '12 dpmm (300 dpi)'),
        ('24dpmm', '24 dpmm (600 dpi)'),
    ], default='8dpmm', required=True)
    labelary_url = fields.Char(default='http://api.labelary.com/v1/printers/')
    width = fields.Float(default=4, required=True)
    height = fields.Float(default=6, required=True)
    measurement = fields.Selection([
        ('inch', 'inches'), ('mm', 'mm'), ('cm', 'cm')
    ], default='inch', required=True)
    display_size = fields.Char(compute='_compute_display_size', store=True)

    @property
    def _report_name(self):
        name = re.sub(f'[{punctuation}]', '', self.name.lower())
        name = re.sub(r'\s', '_', name)
        return f'zpl_label_template.{name}'

    def _create_report(self):
        if not self.report_view_id:
            self.report_view_id = self.env['ir.ui.view'].create([{
                'name': self._report_name,
                'type': 'qweb',
                'key': self._report_name,
                'priority': 16,
                'mode': 'primary',
                'arch_base': self.zpl_code or self._report_default_value(),
            }])

        if not self.report_id:
            self.report_id = self.env['ir.actions.report'].create([{
                'name': self.name,
                'model': self.model_id.model,
                'report_type': 'qweb-text',
                'report_name': self.report_view_id.key,
            }])

    @api.model
    def create(self, values):
        record_id = super(ZPLLabelTemplate, self).create(values)
        record_id._create_report()
        return record_id

    def copy(self, default=None):
        if type(default) != dict:
            default = {}
        if not default.get('name'):
            default['name'] = f'{self.name} (Copy:{self.id})'
        return super(ZPLLabelTemplate, self).copy(default)

    def write(self, values):
        response = super(ZPLLabelTemplate, self).write(values)
        if values.get('model_id'):
            for rec in self:
                rec.report_id.model = rec.model_id.model
        return response

    def toggle_publish(self):
        self.ensure_one()

        if self.published:
            self.report_id.unlink_action()
        else:
            self.report_id.create_action()

    @api.depends('report_id.binding_model_id', 'report_id.binding_type')
    def _compute_published(self):
        for rec in self:
            rec.published = bool(rec.report_id.binding_model_id)

    @property
    def _request_url(self):
        measurements = {'inch': 1, 'mm': 24.5, 'cm': 2.45}
        width = round(self.width / measurements[self.measurement], 4)
        height = round(self.height / measurements[self.measurement], 4)
        return url_join(self.labelary_url, f'{self.dpmm}/labels/{width}x{height}/0/')

    def generate_zpl_image(self):
        record_model_env = self.env[self.model_id.model]
        if self.record_int_id:
            record_id = record_model_env.browse(self.record_int_id)
        else:
            record_id = record_model_env.search([], limit=1)

        q_context = self.report_id._get_eval_context()

        try:
            zpl_preview_code = self.report_view_id._render({
                **q_context,
                'docs': record_id,
                'env': self.env
            })
        except Exception as exp:
            message = exp.message if hasattr(exp, 'message') else exp
            raise UserError(message) from exp

        response = requests.post(
            self._request_url,
            headers={'Accept': 'image/png'},
            files={'file': zpl_preview_code},
            stream=True
        )

        try:
            response.raise_for_status()
        except HTTPError as error:
            raise UserError(error.response.content or error) from error

        self.zpl_image = base64.b64encode(response.content)

    def open_related_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.actions.report',
            'view_mode': 'form',
            'res_id': self.report_id.id,
            'views': [(False, 'form')],
        }

    @api.depends('width', 'height', 'measurement')
    def _compute_display_size(self):
        for record in self:
            record.display_size = f'{record.width}x{record.height} {record.measurement}'

    def action_remove_with_report(self):
        for record in self:
            record.report_id.unlink_action()
            record.report_id.unlink()
            record.report_view_id.unlink()
            record.unlink()
