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

from odoo import models, fields


class CommonLogLinesEpt(models.Model):
    _inherit = "common.log.lines.ept"

    def woo_product_export_log_line(self, message, model_id, common_log_id=False, product_template_id=False):
        if len(product_template_id) > 1:
            vals = [{
                "message": message,
                "model_id": model_id,
                "log_book_id": False if not common_log_id else common_log_id.id,
                "res_id": False if not product_template_id else product_template_id.id
            } for product_template in product_template_id]
        else:
            vals = {
                "message": message,
                "model_id": model_id,
                "log_book_id": False if not common_log_id else common_log_id.id,
                "res_id": False if not product_template_id else product_template_id.id,
            }
        return self.create(vals)
