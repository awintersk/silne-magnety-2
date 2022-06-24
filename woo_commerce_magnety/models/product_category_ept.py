# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger("WooCommerce")


class WooProductCategoryEpt(models.Model):
    _inherit = 'woo.product.categ.ept'

    name = fields.Char(compute='_compute_name', store=True, translate=False)
    category_id = fields.Many2one('product.category', string='Origin category')

    @api.depends('category_id.name', 'woo_instance_id.woo_lang_id')
    def _compute_name(self):
        for r in self.filtered(lambda r: r.category_id and r.woo_instance_id.woo_lang_id):
            instance_lang = r.woo_instance_id.woo_lang_id
            r.name = r.category_id.with_context(lang=instance_lang.code).name

    def create_or_update_woo_category(self, category, sync_images_with_product, instance):
        category = super(WooProductCategoryEpt, self).create_or_update_woo_category(category, sync_images_with_product, instance)
        category.create_odoo_category()
        return category

    def create_odoo_category(self):
        self.ensure_one()
        parent_id = False
        Category = self.env['product.category']
        if self.parent_id:
            parent_id = self.parent_id.create_odoo_category().id
        data = self.prepare_odoo_category(parent_id)

        if self.category_id:
            instance_lang = self.woo_instance_id.woo_lang_id
            self.category_id.with_context(lang=instance_lang.code).write(data)
        else:
            exist_category = self.search([
                '|', ('woo_categ_id', '=', self.woo_categ_id),
                     ('slug', '=', self.slug),
                ('id', '!=', self.id),
                ('category_id', '!=', False),
            ], limit=1)
            if exist_category:
                self.category_id = exist_category.category_id
            else:
                self.category_id = Category.create(data)
        return self.category_id

    def prepare_odoo_category(self, parent_id):
        data = {
            'name': self.name,
            'parent_id': parent_id,
        }
        return data
