# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger("WooCommerce")


class WooProductCategoryEpt(models.Model):
    _inherit = 'woo.product.categ.ept'

    category_id = fields.Many2one('product.category')

    def create_or_update_woo_category(self, category, sync_images_with_product, instance):
        category = super(WooProductCategoryEpt, self).create_or_update_woo_category(category, sync_images_with_product, instance)
        category.create_odoo_category()
        return category

    def create_odoo_category(self):
        parent_id = False
        Category = self.env['product.category']
        if self.parent_id:
            parent_id = self.parent_id.create_odoo_category().id
        data = self.prepare_odoo_category(parent_id)
        if self.category_id:
            self.category_id.write(data)
        elif not Category.search([('name', '=', data['name'])]):
            self.category_id = Category.create([data])
        return self.category_id

    def prepare_odoo_category(self, parent_id):
        data = {
            'name': self.name,
            'parent_id': parent_id,
        }
        return data
