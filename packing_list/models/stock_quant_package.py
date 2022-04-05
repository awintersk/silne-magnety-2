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

from io import BytesIO
from base64 import encodebytes

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.misc import xlsxwriter

_logger = logging.getLogger(__name__)


class XLSXContent:
    __output: BytesIO
    workbook: xlsxwriter.Workbook
    content: bytes = b''
    is_open: bool = False

    def __init__(self):
        self.__output = BytesIO()
        self.workbook = xlsxwriter.Workbook(self.__output, {'in_memory': True})
        self.is_open = True

    def save(self) -> None:
        if self.is_open:
            self.workbook.close()
            self.content = self.__content()
            self.__output.close()
            self.is_open = False

    def __content(self) -> bytes:
        self.__output.seek(0)
        return encodebytes(self.__output.getvalue())


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    document_ids = fields.One2many(
        comodel_name='documents.document',
        compute='_compute_document_ids',
    )
    document_count = fields.Integer(compute='_compute_document_count')
    sale_ids = fields.Many2many(
        comodel_name='sale.order',
        compute='_compute_sale_ids',
        store=True,
    )

    def _compute_document_ids(self):
        for pack_id in self:
            pack_id.document_ids = self.env['documents.document'].search([
                ('res_model', '=', pack_id._name),
                ('res_id', '=', pack_id.id)
            ])

    @api.depends('document_ids')
    def _compute_document_count(self):
        for pack_id in self:
            pack_id.document_count = len(pack_id.document_ids)

    @api.depends('quant_ids.quantity')
    def _compute_sale_ids(self):
        move_line_env = self.env['stock.move.line']
        for pack_id in self:
            move_line_ids = move_line_env.search([('result_package_id', '=', pack_id.id)])
            pack_id.sale_ids = move_line_ids.move_id.sale_line_id.order_id

    def _generate_currier_document(self) -> list:
        folder_id = self.env.ref('packing_list.package_folder')
        document_env = self.env['documents.document']
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = []

        for pack_id in self:
            document_name = f"Package Currier ({pack_id.name})"

            xlsx_data = XLSXContent()
            worksheet = xlsx_data.workbook.add_worksheet(pack_id.name)
            worksheet.write(0, 0, pack_id.name)
            xlsx_data.save()

            document_id = pack_id.document_ids.filtered(lambda doc_id: doc_id.name == document_name)

            if document_id:
                document_id.write({
                    'folder_id': folder_id.id,
                    'datas': xlsx_data.content,
                    'mimetype': mimetype,
                })
            else:
                document_id = document_env.create({
                    'name': document_name,
                    'folder_id': folder_id.id,
                    'datas': xlsx_data.content,
                    'mimetype': mimetype,
                    'res_model': 'stock.quant.package',
                    'res_id': pack_id.id,
                })
                response.append(document_id.id)

        return response

    def action_generate_currier_document(self) -> dict:
        self._generate_currier_document()
        self.invalidate_cache(['document_ids'])
        return self.action_documents()

    def action_documents(self) -> dict:
        return {
            'name': _('Documents'),
            'domain': [('id', 'in', self.document_ids.ids)],
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'views': [(False, 'kanban'), (False, 'list')],
            'view_mode': 'kanban,list',
        }
