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


class WooTagsEpt(models.Model):
    _inherit = 'woo.tags.ept'

    tag_id = fields.Many2one('product.template.tag', string='Tag')
    name = fields.Char(compute='_compute_name', store=True, translate=False)

    def _compute_name(self):
        for r in self.filtered(lambda r: r.tag_id and r.woo_instance_id.woo_lang_id):
            instance_lang = r.woo_instance_id.woo_lang_id
            r.name = r.tag_id.with_context(lang=instance_lang.code).name
