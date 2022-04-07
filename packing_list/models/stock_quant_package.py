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
from odoo.addons.packing_list.excel_tools.xlsx_manager import XLSXContentManager

XLSX_MIMETYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

_logger = logging.getLogger(__name__)


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
        store=False,
    )

    # --------- #
    #  Compute  #
    # --------- #

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

    # --------- #
    #  Actions  #
    # --------- #

    def action_generate_currier_document(self) -> dict:
        self._generate_currier_documents()
        self.invalidate_cache(['document_ids'])
        return self.action_documents()

    def action_documents(self) -> dict:
        action_name = _('Documents')
        self_name = ', '.join(self.mapped('name'))
        return {
            'name': f"{action_name} ({self_name})",
            'domain': [('id', 'in', self.document_ids.ids)],
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'views': [(False, 'kanban'), (False, 'list')],
            'view_mode': 'kanban,list',
        }

    # ----------- #
    #  Protected  #
    # ----------- #

    def _generate_currier_documents(self):
        folder_id = self.env.ref('packing_list.package_folder')
        document_env = self.env['documents.document']

        for pack_id in self:
            document_name = f"Package Currier ({pack_id.name})"

            datas = self._compile_xlsx_datas()
            document_id = pack_id.document_ids.filtered(lambda doc_id: doc_id.name == document_name)

            if document_id:
                document_id.write({
                    'folder_id': folder_id.id,
                    'datas': datas,
                    'mimetype': XLSX_MIMETYPE,
                })
            else:
                document_env.create({
                    'name': document_name,
                    'folder_id': folder_id.id,
                    'datas': datas,
                    'mimetype': XLSX_MIMETYPE,
                    'res_model': 'stock.quant.package',
                    'res_id': pack_id.id,
                })

    def _compile_xlsx_datas(self) -> bytes:
        self.ensure_one()
        headers = [
            'dobierka', 'meno_prijemcu', 'ulica_prijemcu', 'mesto_prijemcu',
            'psc_prijemcu', 'stat_prijemcu', 'telefon_prijemcu',
            'meno_odosielatela', 'ulica_odosielatela', 'mesto_odosielatela',
            'psc_odosielatela', 'stat_odosielatela', 'telefon_odosielatela',
            'variabilny_symbol', 'referencne_cislo', 'pocet_balikov',
            'sms_cislo', 'email_prijemcu', 'sluzba', 'obsah', 'vaha',
        ]
        with XLSXContentManager(headers) as xlsx_data:
            xlsx_data.create_switch_worksheet(self.name)
            xlsx_data.header_format = xlsx_data.workbook.add_format({
                'bg_color': 'yellow',
                'border': 1,
            })
            xlsx_data.write_headers()
            for sale_id in self.sale_ids:
                partner_id = sale_id.partner_id
                sale_partner_id = sale_id.user_id.partner_id
                xlsx_data.write_dict({
                    'dobierka': sale_id.amount_total,
                    'meno_prijemcu': partner_id.name,
                    'ulica_prijemcu': partner_id.street or partner_id.street2,
                    'mesto_prijemcu': partner_id.city,
                    'psc_prijemcu': partner_id.zip,
                    'stat_prijemcu': '',
                    'telefon_prijemcu': partner_id.phone or partner_id.mobile,
                    'meno_odosielatela': sale_partner_id.name,
                    'ulica_odosielatela': sale_partner_id.street or sale_partner_id.street2,
                    'mesto_odosielatela': sale_partner_id.city,
                    'psc_odosielatela': sale_partner_id.zip,
                    'stat_odosielatela': sale_partner_id.country_id.name,
                    'telefon_odosielatela': sale_partner_id.phone or sale_partner_id.mobile,
                    'variabilny_symbol': '',
                    'referencne_cislo': '',
                    'pocet_balikov': '',
                    'sms_cislo': sale_partner_id.phone or sale_partner_id.mobile,
                    'email_prijemcu': partner_id.email_normalized,
                    'vaha': self.weight,
                })
        return xlsx_data.content
