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
            woo_product_template_id, template_title = data.get("id"), data.get("name")
            woo_template = self.with_context(active_test=False).search(
                [("woo_tmpl_id", "=", woo_product_template_id), ("woo_instance_id", "=", woo_instance.id)], limit=1)
            categ = data['categories'][0]
            woo_category = self.env['woo.product.categ.ept'].search([('woo_categ_id', '=', categ['id'])], limit=1)
            if woo_category.category_id:
                woo_template.product_tmpl_id.categ_id = woo_category.category_id
            if data["attributes"]:
                woo_template.sync_attributes(data["attributes"])
        return res

    @api.model
    def sync_attributes(self, attributes):
        WooAttribute = self.env['woo.product.attribute.ept']
        Attribute = self.env['product.attribute.value']
        product = self.product_tmpl_id
        if product:
            attribute_list = []
            for attr in attributes:
                if not attr['variation']:
                    attribute = WooAttribute.search([
                        ('woo_attribute_id', '=', attr['id'])
                    ], limit=1).attribute_id
                    exist_attribute = product.attribute_line_ids.mapped('attribute_id').ids
                    if attribute:
                        value = Attribute.search([
                            ('attribute_id', '=', attribute.id),
                            ('name', 'in', attr['options']),
                        ], limit=1)
                        if attribute.id not in exist_attribute:
                            data = {
                                'product_tmpl_id': product.id,
                                'attribute_id': attribute.id,
                                'value_ids': [(6, 0, value.ids)]
                            }
                            attribute_list.append((0, 0, data))
                        else:
                            attribute_for_update = product.attribute_line_ids.filtered(
                                lambda x: x.attribute_id == attribute.id
                                          and x.value_ids[0].name not in value.mapped('name'))
                            if attribute_for_update:
                                data = {
                                    'value_ids': [(6, 0, value.ids)]
                                }
                                attribute_list.append((1, attribute_for_update[0].id, data))

            if attribute_list:
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
