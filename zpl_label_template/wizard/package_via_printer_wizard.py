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

from odoo import models, fields


class PackageViaPrinterWizard(models.TransientModel):
    _name = 'package.via.printer.wizard'
    _description = 'Package Via Printer Wizard'

    report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        required=True,
        domain=[
            ('model', '=', 'stock.quant.package'),
            ('report_type', 'in', ('qweb-pdf', 'qweb-text')),
        ],
    )
    printer_id = fields.Many2one('printnode.printer', required=True)
    repeat = fields.Integer(default=1, required=True)
    package_ids = fields.One2many(
        comodel_name='stock.quant.package',
        store=False,
        required=True,
    )

    def print(self):
        repeat = self.repeat if self.repeat else 1
        for idx in range(repeat):
            self.printer_id.printnode_print(self.report_id, self.package_ids)
