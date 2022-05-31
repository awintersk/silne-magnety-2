# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    name = fields.Char(
        translate=True,
    )

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        self = self.with_context(lang=self.env.user.lang)
        return super(ProductCategory, self)._compute_complete_name()
