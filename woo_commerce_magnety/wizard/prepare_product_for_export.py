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
