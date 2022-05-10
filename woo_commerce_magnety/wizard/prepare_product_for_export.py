# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import logging
from odoo import models, fields, _

_logger = logging.getLogger("WooCommerce")


class PrepareProductForExport(models.TransientModel):
    _inherit = "woo.prepare.product.for.export.ept"

    def prepare_woo_template_layer_vals(self, woo_instance, product_template, product_type):
        data = super(PrepareProductForExport, self).prepare_woo_template_layer_vals(woo_instance, product_template, product_type)
        if len(product_template.product_variant_ids) == 1:
            data.update({
                'woo_product_type': 'simple',
            })
        return data

    def create_update_woo_template(self, variant, woo_instance, woo_template_id, woo_category_dict):
        woo_template_id = super(PrepareProductForExport, self).create_update_woo_template(variant, woo_instance, woo_template_id, woo_category_dict)
        product_template = variant.product_tmpl_id
        if product_template.categ_ids:
            categories = []
            for categ in product_template.categ_ids:
                self.create_categ_in_woo(categ, woo_instance.id, woo_category_dict)
                woo_categ = self.update_category_info(categ, woo_instance.id)
                categories.append(woo_categ.id)
            self.env["woo.product.template.ept"].browse(woo_template_id).write(
                {'woo_categ_ids': [(4, c) for c in categories]})
        return woo_template_id
