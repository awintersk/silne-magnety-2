# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger("WooCommerce")


class WooProductTemplateEpt(models.Model):
    _inherit = "woo.product.template.ept"

    @api.model
    def sync_products(self, *args, **kwargs):
        self = self.with_context(lang=self.woo_instance_id.woo_lang_id.code)
        product_data_queue_lines, woo_instance, common_log_book_id, skip_existing_products = args[:4]
        order_queue_line = kwargs.get('order_queue_line')
        res = super(WooProductTemplateEpt, self).sync_products(product_data_queue_lines, woo_instance, common_log_book_id, skip_existing_products, **kwargs)
        for product_data_queue_line in product_data_queue_lines:
            data, product_queue_id, product_data_queue_line, sync_category_and_tags = self.prepare_product_response(order_queue_line, product_data_queue_line)
            woo_product_template_id, template_title = data.get("id"), data.get("name")
            woo_template = self.with_context(active_test=False).search(
                [("woo_tmpl_id", "=", woo_product_template_id), ("woo_instance_id", "=", woo_instance.id)], limit=1)
            categories = []
            for category_data in data['categories']:
                woo_category = self.env['woo.product.categ.ept'].search([('woo_categ_id', '=', category_data['id'])], limit=1)
                if not woo_category.category_id:
                    odoo_category = woo_category.create_odoo_category()
                else:
                    odoo_category = woo_category.category_id
                if odoo_category:
                    categories.append(odoo_category.id)
            if categories:
                woo_template.product_tmpl_id.categ_ids = [(6, 0, categories)]
                woo_template.product_tmpl_id.categ_id = categories[0]
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
                        ('woo_attribute_id', '=', attr['id']),
                        ('woo_instance_id', '=', self.woo_instance_id.id),
                    ], limit=1).attribute_id
                    exist_attribute = product.attribute_line_ids.mapped('attribute_id').ids
                    if attribute:
                        value = Attribute.search([
                            ('attribute_id', '=', attribute.id),
                            ('name', 'in', attr['options']),
                        ], limit=1)
                        if value:  # TODO need checking language(can't find some values)
                            if attribute.id not in exist_attribute:
                                data = {
                                    'product_tmpl_id': product.id,
                                    'attribute_id': attribute.id,
                                    'value_ids': [(6, 0, value.ids)]
                                }
                                attribute_list.append((0, 0, data))
                            else:
                                attribute_for_update = product.attribute_line_ids.filtered(
                                    lambda x: x.attribute_id.id == attribute.id
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

    def prepare_product_update_data(self, template, update_image, update_basic_detail, data):
        flag, data = super(WooProductTemplateEpt, self).prepare_product_update_data(template, update_image, update_basic_detail, data)
        attributes = []
        if template.product_tmpl_id.attribute_line_ids and len(template.product_tmpl_id.product_variant_ids) == 1:
            position = 0
            for attribute_line in template.product_tmpl_id.attribute_line_ids:
                options = []
                for option in attribute_line.value_ids:
                    options.append(option.name)
                variation = False
                if attribute_line.attribute_id.create_variant in ['always', 'dynamic']:
                    variation = True
                attribute_data = {
                    'name': attribute_line.attribute_id.name, 'slug': attribute_line.attribute_id.name.lower(),
                    'position': position, 'visible': True, 'variation': variation, 'options': options
                }
                position += 1
                attributes.append(attribute_data)
        data['attributes'] = attributes
        return flag, data

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
