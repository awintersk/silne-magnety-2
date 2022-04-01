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

    def get_product_attribute(self, template, instance, common_log_id, model_id):
        attributes, is_variable = super(WooProductTemplateEpt, self).get_product_attribute(template, instance, common_log_id, model_id)
        if len(template.product_variant_ids) == 1:
            for attribute in attributes:
                attribute.update({
                    'variation': False
                })
                is_variable = False
        return attributes, is_variable

    def prepare_product_data(self, woo_template, publish, update_price,
                             update_image, basic_detail, common_log_id, model_id):
        data = super(WooProductTemplateEpt, self).prepare_product_data(
            woo_template, publish, update_price, update_image,
            basic_detail, common_log_id, model_id)
        if len(woo_template.product_tmpl_id.product_variant_ids) == 1:
            data.update({
                'variations': [],
                'default_attributes': [],
            })
        return data

    def simple_product_sync(self,
                            woo_instance,
                            product_response,
                            common_log_book_id,
                            product_queue_id,
                            product_data_queue_line,
                            template_updated,
                            skip_existing_products,
                            order_queue_line):
        woo_template_id = super(WooProductTemplateEpt, self).simple_product_sync(
            woo_instance,
            product_response,
            common_log_book_id,
            product_queue_id,
            product_data_queue_line,
            template_updated,
            skip_existing_products,
            order_queue_line
        )

        product_tmpl_id = woo_template_id.product_tmpl_id if woo_template_id else None

        if product_tmpl_id and not product_response.get('weight'):
            product_tmpl_id._pull_product_weight_from_attribute()

        return woo_template_id
