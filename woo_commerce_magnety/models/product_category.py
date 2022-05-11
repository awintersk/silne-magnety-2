# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    name = fields.Char(
        translate=True,
    )
