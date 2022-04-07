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

from odoo import models, fields, api, _
from odoo.addons.packing_list.excel_tools.xlsx_manager import XLSXContentManager

XLSX_MIMETYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


class PackingListWizard(models.TransientModel):
    _name = 'packing.list.wizard'
    _description = 'Packing List Wizard'

    name = fields.Char(required=True, readonly=True)
    package_ids = fields.One2many(
        comodel_name='stock.quant.package',
        store=False,
        readonly=True,
    )
    sale_ids = fields.One2many(
        comodel_name='sale.order',
        store=False,
        readonly=True,
    )
    document_ids = fields.One2many(
        comodel_name='documents.document',
        store=False,
    )

    # ---------- #
    #  Defaults  #
    # ---------- #

    @api.model
    def default_get(self, default_fields):
        package_env = self.env['stock.quant.package']
        response = super(PackingListWizard, self).default_get(default_fields)
        sale_int_ids = self._context.get('sale_ids', [])
        package_int_ids = self._context.get('package_ids', [])

        if sale_int_ids:
            package_ids = package_env.search([
                ('packaging_id.packing_type', '=', 'pallet'),
                ('sale_ids.state', 'in', ('sale', 'done')),
                ('sale_ids', 'in', sale_int_ids),
            ])
        elif package_int_ids:
            package_ids = package_env.search([
                ('packaging_id.packing_type', '=', 'pallet'),
                ('sale_ids.state', 'in', ('sale', 'done')),
                ('id', 'in', package_int_ids)
            ])
        else:
            return {}

        if package_ids:
            return dict(
                response,
                name=f"Package Currier ({','.join(package_ids.mapped('name'))})",
                package_ids=[(6, 0, package_ids.ids)],
                sale_ids=[(6, 0, self.package_ids.sale_ids.ids)],
            )

        return {}

    # --------- #
    #  Actions  #
    # --------- #

    def action_documents(self) -> dict:
        action_name = _('Documents')
        self_name = ','.join(self.package_ids.mapped('name'))
        return {
            'name': f"{action_name} ({self_name})",
            'domain': [('id', 'in', self.document_ids.ids)],
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'views': [(False, 'kanban'), (False, 'list')],
            'view_mode': 'kanban,list',
        }

    def action_generate(self):
        self._generate_packing_documents(
            datas=self._compile_currier_xlsx_datas()
        )
        return self.action_documents()

    # --------- #
    #  Private  #
    # --------- #

    def _generate_packing_documents(self, datas: bytes):
        folder_id = self.env.ref('packing_list.package_folder')
        document_env = self.env['documents.document']

        self.document_ids = self.package_ids.document_ids.filtered(lambda doc_id: doc_id.name == self.name)

        if self.document_ids:
            self.document_ids.write({
                'folder_id': folder_id.id,
                'datas': datas,
                'mimetype': XLSX_MIMETYPE,
            })
        else:
            self.document_ids = document_env.create({
                'name': self.name,
                'folder_id': folder_id.id,
                'datas': datas,
                'mimetype': XLSX_MIMETYPE,
                'package_ids': self.package_ids.ids,
            })

    def _compile_currier_xlsx_datas(self) -> bytes:
        headers = [
            'dobierka', 'meno_prijemcu', 'ulica_prijemcu', 'mesto_prijemcu',
            'psc_prijemcu', 'stat_prijemcu', 'telefon_prijemcu',
            'meno_odosielatela', 'ulica_odosielatela', 'mesto_odosielatela',
            'psc_odosielatela', 'stat_odosielatela', 'telefon_odosielatela',
            'variabilny_symbol', 'referencne_cislo', 'pocet_balikov',
            'sms_cislo', 'email_prijemcu', 'sluzba', 'obsah', 'vaha',
        ]
        with XLSXContentManager(headers) as xlsx_data:
            xlsx_data.create_switch_worksheet(','.join(self.mapped('name')))
            xlsx_data.header_format = xlsx_data.workbook.add_format({
                'bg_color': 'yellow',
                'border': 1,
            })
            xlsx_data.write_headers()
            for sale_id in self.package_ids.sale_ids:
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
                    'vaha': sum(sale_id.order_line.product_id.mapped('weight')),
                })
        return xlsx_data.content
