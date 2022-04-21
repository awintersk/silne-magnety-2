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


from xlsxwriter import Workbook
from logging import getLogger

from odoo import models, _
from odoo.exceptions import UserError

_logger = getLogger(__name__)


class StockQuantPackageCurrierReport(models.AbstractModel):
    _name = 'report.stock.quant.package.currier'
    _description = 'Stock Quant Package Currier Report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, package_ids):
        """
            :param Workbook workbook: Workbook
            :param dict data: Dictionary
            :param models.BaseModel package_ids:
        """
        pass
