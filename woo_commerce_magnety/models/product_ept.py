# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger("WooCommerce")


class WooProductTemplateEpt(models.Model):
    _inherit = "woo.product.template.ept"

    @api.model
    def sync_products(self, *args, **kwargs):
        product_data_queue_lines, woo_instance, common_log_book_id, skip_existing_products = args[:4]
        order_queue_line = kwargs.get('order_queue_line')
        res = super(WooProductTemplateEpt, self).sync_products(product_data_queue_lines, woo_instance, common_log_book_id, skip_existing_products, **kwargs)
        for product_data_queue_line in product_data_queue_lines:
            data, product_queue_id, product_data_queue_line, sync_category_and_tags = self.prepare_product_response(order_queue_line, product_data_queue_line)
            if data["attributes"]:
                woo_product_template_id, template_title = data.get("id"), data.get("name")
                woo_template = self.with_context(active_test=False).search(
                    [("woo_tmpl_id", "=", woo_product_template_id), ("woo_instance_id", "=", woo_instance.id)], limit=1)
                woo_template.sync_attributes(data["attributes"])
        return res

    @api.model
    def sync_attributes(self, attributes):
        product = self.product_tmpl_id
        if product:
            attribute_list = []
            for attr in attributes:
                if not attr['variation']:
                    attribute = self.env['woo.product.attribute.ept'].search([
                        ('woo_attribute_id', '=', attr['id'])
                    ], limit=1)
                    if attribute:
                        attribute = attribute.attribute_id
                        value = self.env['product.attribute.value'].search([
                            ('attribute_id', '=', attribute.id),
                            ('name', 'in', attr['options']),
                        ])
                        data = {
                            'product_tmpl_id': product.id,
                            'attribute_id': attribute.id,
                            'value_ids': [(6, 0, value.ids)]
                        }
                        attribute_list.append((0, 0, data))
            if attribute_list:
                attribute_list.insert(0, (5, 0))
                product.write({
                    'attribute_line_ids': attribute_list
                })
