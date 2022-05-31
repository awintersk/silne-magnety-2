# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import logging
from collections import defaultdict

from odoo import models, fields, api, _
from .product_pricelist import NUMBER_OF_BULK
from odoo.exceptions import UserError

_logger = logging.getLogger("WooCommerce")


class WooProductTemplateEpt(models.Model):
    _inherit = "woo.product.template.ept"

    name = fields.Char(related='product_tmpl_id.name')

    @api.model
    def sync_products(self, *args, **kwargs):
        self = self.with_context(lang=self.woo_instance_id.woo_lang_id.code)
        product_data_queue_lines, woo_instance, common_log_book_id = args[:3]
        order_queue_line = kwargs.get('order_queue_line')
        skip_existing_products = kwargs.get('skip_existing_products')
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

    def prepare_product_variant_dict(self, instance, template, data, basic_detail, update_price,
                                     update_image, common_log_id, model_id):
        self.env['woo.product.template.ept'].update_woo_attributes(
            template, instance, common_log_id)
        self.env['woo.product.template.ept'].update_woo_attribute_values(
            template, instance, common_log_id)
        data, flag = super(WooProductTemplateEpt, self).prepare_product_variant_dict(
            instance, template, data, basic_detail, update_price, update_image, common_log_id, model_id)

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

        # Bulk Prices
        if update_price and len(template.product_tmpl_id.product_variant_ids) == 1:
            product = template.product_tmpl_id.product_variant_ids
            bulk_data = []
            Price = self.env['product.pricelist.item']
            instance_price = template.woo_instance_id.woo_pricelist_id
            bulk_prices = Price.search([
                ('pricelist_id', '=', instance_price.id),
                ('applied_on', '=', '0_product_variant'),
                ('compute_price', '=', 'fixed'),
                ('product_id', '=', product.id),
                ('bulk_discount', '!=', 'base_price'),
            ], order='bulk_discount')
            if bulk_prices:
                base_price = Price.search([
                    ('pricelist_id', '=', instance_price.id),
                    ('applied_on', '=', '0_product_variant'),
                    ('compute_price', '=', 'fixed'),
                    ('product_id', '=', product.id),
                    ('bulk_discount', '=', 'base_price'),
                ], limit=1)
                for price in bulk_prices:
                    bulk_data += [{
                        'key': f'_bulkdiscount_quantity_{price.bulk_discount[-1]}',
                        'value': price.min_quantity,
                    }, {
                        'key': f'_bulkdiscount_discount_fixed_{price.bulk_discount[-1]}',
                        'value': round(base_price.fixed_price - price.fixed_price, 2),
                    }]
            if bulk_data:
                bulk_data.append({'key': '_bulkdiscount_enabled', 'value': 'yes'})
                if data.get('meta_data', False):
                    data['meta_data'] += bulk_data
                else:
                    data['meta_data'] = bulk_data
        else:
            pass
        return data, flag

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

        meta_data = product_response["meta_data"]
        if woo_instance.sync_price_with_product and meta_data:
            product_sku = product_response["sku"]
            woo_product, odoo_product = self.search_odoo_product_variant(woo_instance, product_sku, product_response.get("id"))
            def get_value(data_list, key):
                for data in data_list:
                    if data.get('key') == key:
                        return data['value']
                return False

            if get_value(meta_data, '_bulkdiscount_enabled') == 'yes':
                Price = self.env['product.pricelist.item']
                product = woo_product.product_id
                instance_price = woo_instance.woo_pricelist_id
                price_data = []
                base_price = Price.search([
                    ('pricelist_id', '=', instance_price.id),
                    ('applied_on', '=', '0_product_variant'),
                    ('compute_price', '=', 'fixed'),
                    ('product_id', '=', product.id),
                    ('bulk_discount', '=', 'base_price'),
                ], limit=1)
                if base_price:
                    for i in range(1, NUMBER_OF_BULK):
                        min_quantity = get_value(meta_data, f'_bulkdiscount_quantity_{i}')
                        discount = get_value(meta_data, f'_bulkdiscount_discount_fixed_{i}')
                        if min_quantity and discount:
                            min_quantity = int(min_quantity)
                            discount = float(discount)
                            bulk_price = base_price.fixed_price - discount
                            exist_price = Price.search([
                                ('pricelist_id', '=', instance_price.id),
                                ('applied_on', '=', '0_product_variant'),
                                ('compute_price', '=', 'fixed'),
                                ('product_id', '=', product.id),
                                ('bulk_discount', '=', f'bulk_discount_{i}'),
                            ])
                            if exist_price:
                                exist_price.write({
                                    'fixed_price': bulk_price,
                                    'min_quantity': min_quantity,
                                })
                            else:
                                price_data.append({
                                    'product_id': product.id,
                                    'applied_on': '0_product_variant',
                                    'compute_price': 'fixed',
                                    'min_quantity': min_quantity,
                                    'fixed_price': bulk_price,
                                    'pricelist_id': woo_instance.woo_pricelist_id.id,
                                    'bulk_discount': f'bulk_discount_{i}',
                                })
                if price_data:
                    Price.create(price_data)

        return woo_template_id

    @api.model
    def update_products_in_woo(self, instance, templates, update_price, publish, update_image,
                               update_basic_detail, common_log_id):
        templates = templates.with_context(lang=instance.woo_lang_id.code)
        res = super(
            WooProductTemplateEpt,
            self.with_context(lang=instance.woo_lang_id.code)
        ).update_products_in_woo(
            instance, templates, update_price, publish, update_image,
            update_basic_detail, common_log_id,
        )

        categories = templates.woo_categ_ids.filtered('exported_in_woo')
        self.env['woo.product.categ.ept'].update_product_categs_in_woo( instance, categories)

        return res

    def _prepare_attributes_data(self, instance):
        WooAttr = self.env['woo.product.attribute.ept']
        attrs_to_update = self.product_tmpl_id.attribute_line_ids.attribute_id
        woo_attrs = WooAttr.search([
            ('woo_instance_id', '=', instance.id),
            ('attribute_id', 'in', attrs_to_update.ids),
            ('exported_in_woo', '=', True),
        ])
        return [{
            'id': attr.woo_attribute_id,
            'name': attr.name,
            'slug': attr.slug,
        } for attr in woo_attrs]

    def _prepare_attribute_term_data(self, instance):
        WooTerm = self.env['woo.product.attribute.term.ept']
        terms_to_update = self.product_tmpl_id.attribute_line_ids.value_ids
        # TODO: investigate term types
        woo_terms_to_update = WooTerm.read_group(
            domain=[
                ('woo_instance_id', '=', self.woo_instance_id.id),
                ('attribute_value_id', 'in', terms_to_update.ids),
                ('exported_in_woo', '=', True),
            ],
            fields=['woo_attribute_id', 'ids:array_agg(id)'],
            groupby=['woo_attribute_id'],
        )
        res = defaultdict(list)
        for woo_attribute in woo_terms_to_update:
            for woo_term_id in woo_attribute['ids']:
                woo_term = WooTerm.browse(woo_term_id)
                res[woo_term['woo_attribute_id']].append({
                    'id': woo_term['woo_attribute_term_id'],
                    'name': woo_term['name'],
                    'slug': woo_term['slug'],
                    'description': woo_term['description'],
                })
        return res

    def update_woo_attributes(self, template, instance, common_log_id):
        common_log_line_obj = self.env["common.log.lines.ept"]
        model_id = common_log_line_obj.get_model_id('woo.product.attribute.term.ept')
        url = 'products/attributes/batch'
        attribute_data = template._prepare_attributes_data(instance)
        wc_api = instance.woo_connect()
        try:
            res = wc_api.put(url, data={'update': attribute_data})
        except Exception as error:
            raise UserError(_("Something went wrong while exporting Attribute Terms."
                                "\n\nPlease Check your Connection and"
                                "Instance Configuration.\n\n" + str(error)))
        self.check_woocommerce_response(res, "Export Product Attributes", model_id,
                                        common_log_id, template)

    def update_woo_attribute_values(self, template, instance, common_log_id):
        common_log_line_obj = self.env["common.log.lines.ept"]
        model_id = common_log_line_obj.get_model_id('woo.product.attribute.term.ept')
        url = 'products/attributes/%s/terms/batch'
        data = template._prepare_attribute_term_data(instance)
        wc_api = instance.woo_connect()
        for woo_attribute_id, term_data in data.items():
            try:
                res = wc_api.put(url % woo_attribute_id, data={'update': term_data})
            except Exception as error:
                raise UserError(_("Something went wrong while exporting Attribute Terms."
                                  "\n\nPlease Check your Connection and"
                                  "Instance Configuration.\n\n" + str(error)))
            self.check_woocommerce_response(res, "Export Product Attribute Terms",
                                            model_id, common_log_id, template)
