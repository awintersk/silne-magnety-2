# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import logging
from collections import defaultdict
from datetime import datetime

from odoo import models, fields, api, _
from .product_pricelist import NUMBER_OF_BULK
from odoo.exceptions import UserError

_logger = logging.getLogger("WooCommerce")


class WooProductTemplateEpt(models.Model):
    _inherit = "woo.product.template.ept"

    name = fields.Char(
        compute=False,
        store=True,
        translate=False,
        inverse='_set_name',
    )

    def _update_translations(self):
        for r in self.filtered(lambda r: r.product_tmpl_id and r.woo_instance_id.woo_lang_id):
            instance_lang = r.woo_instance_id.woo_lang_id
            r.name = r.product_tmpl_id.with_context(lang=instance_lang.code).name

    def _set_name(self):
        for r in self:
            instance_lang = r.woo_instance_id.woo_lang_id
            r.product_tmpl_id.with_context(lang=instance_lang.code).name = r.name

    @api.model
    def sync_products(self, *args, **kwargs):
        product_data_queue_lines, woo_instance, common_log_book_id = args[:3]
        self = self.with_context(lang=woo_instance.woo_lang_id.code)
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
        self = self.with_context(lang=woo_instance.woo_lang_id.code)

        common_log_line_obj = self.env["common.log.lines.ept"]
        woo_template_id = odoo_template = sync_category_and_tags = False
        model_id = common_log_line_obj.get_model_id(self._name)
        update_price = woo_instance.sync_price_with_product
        update_images = woo_instance.sync_images_with_product
        template_title = product_response.get("name")
        woo_product_template_id = product_response.get("id")
        product_sku = product_response["sku"]
        variant_price = product_response.get("regular_price") or product_response.get("sale_price") or 0.0
        template_info = self.prepare_template_vals(woo_instance, product_response)

        if order_queue_line:
            sync_category_and_tags = True
        if not product_sku:
            message = """Value of SKU/Internal Reference is not set for product '%s', in the Woocommerce store.""", \
                      template_title
            common_log_line_obj.woo_create_product_log_line(message, model_id,
                                                            product_data_queue_line if not order_queue_line
                                                            else order_queue_line, common_log_book_id)
            _logger.info("Process Failed of Product %s||Queue %s||Reason is %s", woo_product_template_id,
                         product_queue_id, message)
            if not order_queue_line:
                product_data_queue_line.write({"state": "failed", "last_process_date": datetime.now()})
            return False

        woo_product, odoo_product = self.search_odoo_product_variant(woo_instance, product_sku, woo_product_template_id)

        if woo_product and not odoo_product:
            woo_template_id = woo_product.woo_template_id
            odoo_product = woo_product.product_id
            if skip_existing_products:
                product_data_queue_line.state = "done"
                return False

        if odoo_product:
            odoo_template = odoo_product.product_tmpl_id

        is_importable, message = self.is_product_importable(product_response, odoo_product, woo_product)
        if not is_importable:
            common_log_line_obj.woo_create_product_log_line(message, model_id,
                                                            product_data_queue_line if not order_queue_line else
                                                            order_queue_line, common_log_book_id)
            _logger.info("Process Failed of Product %s||Queue %s||Reason is %s", woo_product_template_id,
                         product_queue_id, message)
            if not order_queue_line:
                product_data_queue_line.state = "failed"
            return False
        variant_info = self.prepare_woo_variant_vals(woo_instance, product_response)
        if not woo_product:
            if not woo_template_id:
                if not odoo_template and woo_instance.auto_import_product:
                    woo_weight = float(product_response.get("weight") or "0.0")
                    weight = self.convert_weight_by_uom(woo_weight, woo_instance, import_process=True)
                    template_vals = {
                        "name": template_title, "type": "product", "default_code": product_response["sku"],
                        "weight": weight, "invoice_policy": "order"
                    }
                    if self.env["ir.config_parameter"].sudo().get_param("woo_commerce_ept.set_sales_description"):
                        template_vals.update({"woo_description": product_response.get("description", ""),
                                              "woo_short_description": product_response.get("short_description", "")})
                    if product_response["virtual"]:
                        template_vals.update({"type": "service"})
                    odoo_template = self.env["product.template"].create(template_vals)
                    odoo_product = odoo_template.product_variant_ids
                if not odoo_template:
                    message = "%s Template Not found for sku %s in Odoo." % (template_title, product_sku)
                    common_log_line_obj.woo_create_product_log_line(message, model_id,
                                                                    product_data_queue_line if not order_queue_line
                                                                    else order_queue_line, common_log_book_id)
                    _logger.info("Process Failed of Product %s||Queue %s||Reason is %s", woo_product_template_id,
                                 product_queue_id, message)
                    if not order_queue_line:
                        product_data_queue_line.state = "failed"
                    return False

                woo_template_vals = self.prepare_woo_template_vals(template_info, odoo_template.id,
                                                                   sync_category_and_tags, woo_instance,
                                                                   common_log_book_id)
                if product_response["virtual"] and odoo_template.type == 'service':
                    woo_template_vals.update({"is_virtual_product": True})
                    odoo_template.write({"type": "service"})
                woo_template_id = self.create(woo_template_vals)

            variant_info.update({"product_id": odoo_product.id, "woo_template_id": woo_template_id.id})
            woo_product = self.env["woo.product.product.ept"].create(variant_info)
        else:
            if not template_updated:
                woo_template_vals = self.prepare_woo_template_vals(template_info, woo_template_id.product_tmpl_id.id,
                                                                   sync_category_and_tags, woo_instance,
                                                                   common_log_book_id)
                woo_template_id.write(woo_template_vals)
            woo_product.write(variant_info)
        if update_price:
            woo_instance.woo_pricelist_id.set_product_price_ept(woo_product.product_id.id, variant_price)
        if update_images and isinstance(product_queue_id, str) and product_queue_id == 'from Order':
            self.update_product_images(product_response["images"], {}, woo_template_id, woo_product, woo_instance, False)

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
                            try:
                                min_quantity = float(min_quantity)
                                discount = float(discount)
                            except ValueError:
                                continue
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

        if woo_template_id and woo_template_id.woo_tag_ids:
            woo_template_id.woo_tag_ids.update_product_template_tags()
            product_tmpl_id.tag_ids = [(6, 0, woo_template_id.woo_tag_ids.tag_id.ids)]

        return woo_template_id

    def woo_create_variant_product(self, product_template_dict, woo_instance):
        ir_config_parameter_obj = self.env["ir.config_parameter"]
        product_template_obj = self.env['product.template']
        product_template = False
        available_odoo_products = {}

        template_title = ""
        if product_template_dict.get('title'):
            template_title = product_template_dict.get('title')
        elif product_template_dict.get('name'):
            template_title = product_template_dict.get('name')

        attrib_line_vals = self.prepare_woo_attribute_line_vals(product_template_dict.get('attributes'))

        if attrib_line_vals:
            product_template_values = {'name': template_title, 'type': 'product', "invoice_policy": "order",
                                       'attribute_line_ids': attrib_line_vals}
            if ir_config_parameter_obj.sudo().get_param("woo_commerce_ept.set_sales_description"):
                product_template_values.update({"woo_description": product_template_dict.get("description", ""),
                                                "woo_short_description": product_template_dict.get("short_description", "")})

            product_template = product_template_obj.create(product_template_values)
            available_odoo_products = self.woo_set_variant_sku(woo_instance, product_template_dict, product_template,
                                                               woo_instance.sync_price_with_product)
        return product_template, available_odoo_products

    def template_attribute_process(self, woo_instance, odoo_template, variant, template_title, common_log_book_id, data,
                                   product_data_queue_line, order_queue_line):
        """
        This method use to create new attribute if customer only add the attribute value other wise it will create a mismatch logs.
        @param :self,woo_instance,odoo_template,variant,template_title,common_log_book_id,data,product_data_queue_line,order_queue_line
        @return: odoo_product, True
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 21 August 2020.
        Task_id:165892
        """
        common_log_line_obj = self.env["common.log.lines.ept"]
        model_id = common_log_line_obj.get_model_id(self._name)
        if odoo_template.attribute_line_ids:
            # If the new variant has other attribute than available in odoo template, then exception activity will be
            # generated. otherwise it will add new value in current attribute, and will relate with the new odoo
            # variant.
            woo_attribute_ids = []
            odoo_attributes = odoo_template.attribute_line_ids.attribute_id.ids
            for attribute in variant.get("attributes"):
                attribute = self.env["product.attribute"].get_attribute(attribute["name"])
                woo_attribute_ids.append(attribute.id)
            woo_attribute_ids.sort()
            odoo_attributes.sort()
            if odoo_attributes != woo_attribute_ids:
                message = """- Product %s has tried adding a new attribute for sku '%s' in Odoo.
                          - System will not allow adding new attributes to a product.""" % (
                    template_title, variant.get("sku"))
                common_log_line_obj.woo_create_product_log_line(message, model_id,
                                                                product_data_queue_line if not order_queue_line else
                                                                order_queue_line, common_log_book_id)

                if not order_queue_line:
                    product_data_queue_line.state = "failed"
                if woo_instance.is_create_schedule_activity:
                    common_log_book_id.create_woo_schedule_activity()
                return False

            template_attribute_value_domain = self.find_template_attribute_values(data.get("attributes"),
                                                                                  variant.get("attributes"),
                                                                                  odoo_template)
            if not template_attribute_value_domain:
                for woo_attribute in variant.get("attributes"):
                    attribute_id = self.env["product.attribute"].get_attribute(woo_attribute["name"], auto_create=True)
                    value_id = self.env["product.attribute.value"].get_attribute_values(woo_attribute["option"],
                                                                                        attribute_id.id, True)
                    attribute_line = odoo_template.attribute_line_ids.filtered(
                        lambda x: x.attribute_id.id == attribute_id.id)
                    if value_id.id not in attribute_line.value_ids.ids:
                        attribute_line.value_ids = [(4, value_id.id, False)]
                odoo_template._create_variant_ids()
                template_attribute_value_domain = self.find_template_attribute_values(data.get("attributes"),
                                                                                      variant.get("attributes"),
                                                                                      odoo_template)
            odoo_product = self.env["product.product"].search(template_attribute_value_domain)
            if not odoo_product.default_code:
                odoo_product.default_code = variant["sku"]
            return odoo_product

        template_vals = {"name": template_title, "type": "product", "default_code": variant["sku"]}
        if self.env["ir.config_parameter"].sudo().get_param("woo_commerce_ept.set_sales_description"):
            template_vals.update({"woo_description": variant.get("description", "")})

        odoo_product = self.env["product.product"].create(template_vals)
        return odoo_product

    @api.model
    def update_products_in_woo(self, instance, templates, update_price, publish, update_image,
                               update_basic_detail, common_log_id):
        templates = templates.with_context(lang=instance.woo_lang_id.code)

        categories = templates.woo_categ_ids.filtered('exported_in_woo')
        if categories:
            self.env['woo.product.categ.ept'].update_product_categs_in_woo(instance, categories)
        tags = templates.woo_tag_ids.filtered('exported_in_woo')
        if tags:
            self.env['woo.tags.ept'].woo_update_product_tags(instance, tags, common_log_id)
        if templates.product_tmpl_id.attribute_line_ids:
            self.update_woo_attributes(templates, instance, common_log_id)
            self.update_woo_attribute_values(templates, instance, common_log_id)

        res = super(
            WooProductTemplateEpt,
            self.with_context(lang=instance.woo_lang_id.code)
        ).update_products_in_woo(
            instance, templates, update_price, publish, update_image,
            update_basic_detail, common_log_id,
        )

        return res

    def _prepare_attributes_data(self, instance):
        WooAttr = self.env['woo.product.attribute.ept']
        attrs_to_update = self.product_tmpl_id.attribute_line_ids.attribute_id
        woo_attrs = WooAttr.search([
            ('woo_instance_id', '=', instance.id),
            ('attribute_id', 'in', attrs_to_update.ids),
        ])
        data = {'create': [], 'update': []}
        for woo_attr in woo_attrs:
            if woo_attr.exported_in_woo:
                data['update'].append({
                    'id': woo_attr.woo_attribute_id,
                    'name': woo_attr.attribute_id.name,
                    'slug': woo_attr.slug,
                    'type': instance.woo_attribute_type,
                    'variation': woo_attr.attribute_id.create_variant in ['always', 'dynamic'],
                })
            else:
                data['create'].append({
                    'name': woo_attr.attribute_id.name,
                    'slug': woo_attr.slug,
                    'type': instance.woo_attribute_type,
                    'variation': woo_attr.attribute_id.create_variant in ['always', 'dynamic'],
                })
        return data, woo_attrs

    def _prepare_attribute_term_data(self, instance):
        WooTerm = self.env['woo.product.attribute.term.ept']
        terms_to_update = self.product_tmpl_id.attribute_line_ids.value_ids
        woo_terms_to_update = WooTerm.read_group(
            domain=[
                ('woo_instance_id', '=', self.woo_instance_id.id),
                ('attribute_value_id', 'in', terms_to_update.ids),
            ],
            fields=['woo_attribute_id', 'ids:array_agg(id)'],
            groupby=['woo_attribute_id'],
        )
        data = {}
        for woo_attribute in woo_terms_to_update:
            data[woo_attribute['woo_attribute_id']] = {'create': [], 'update': []}
            for woo_term in WooTerm.browse(woo_attribute['ids']):
                if woo_term.exported_in_woo:
                    data[woo_attribute['woo_attribute_id']]['update'].append({
                        'id': woo_term.woo_attribute_term_id,
                        'name': woo_term.attribute_value_id.name,
                        'slug': woo_term.slug,
                        'description': woo_term.description,
                    })
                else:
                    data[woo_attribute['woo_attribute_id']]['create'].append({
                        'name': woo_term.attribute_value_id.name,
                        'slug': woo_term.slug,
                        'description': woo_term.description,
                    })
        return data, WooTerm.browse(
            attr_id for woo_attribute in woo_terms_to_update
                    for attr_id in woo_attribute['ids']
        )

    def update_woo_attributes(self, template, instance, common_log_id):
        common_log_line_obj = self.env["common.log.lines.ept"]
        model_id = common_log_line_obj.get_model_id('woo.product.attribute.term.ept')
        url = 'products/attributes/batch'
        attribute_data, woo_attrs = template._prepare_attributes_data(instance)
        if not attribute_data:
            return
        wc_api = instance.woo_connect()
        try:
            res = wc_api.post(url, data=attribute_data)
        except Exception as error:
            raise UserError(_("Something went wrong while exporting Attribute Terms."
                                "\n\nPlease Check your Connection and"
                                "Instance Configuration.\n\n" + str(error)))
        response_data = self.check_woocommerce_response(res, "Export Product Attributes", model_id,
                                                        common_log_id, template)

        if 'create' not in response_data:
            return

        for attribute in response_data['create']:
            woo_attr = woo_attrs.filtered(lambda x: x.slug == attribute['slug'])
            woo_attr.id = attribute.get('id', False)

    def update_woo_attribute_values(self, template, instance, common_log_id):
        common_log_line_obj = self.env["common.log.lines.ept"]
        model_id = common_log_line_obj.get_model_id('woo.product.attribute.term.ept')
        url = 'products/attributes/%s/terms/batch'
        data, woo_terms = template._prepare_attribute_term_data(instance)
        if not data:
            return
        wc_api = instance.woo_connect()
        for woo_attribute_id, term_data in data.items():
            try:
                res = wc_api.post(url % woo_attribute_id, data=term_data)
            except Exception as error:
                raise UserError(_("Something went wrong while exporting Attribute Terms."
                                  "\n\nPlease Check your Connection and"
                                  "Instance Configuration.\n\n" + str(error)))
            response_data = self.check_woocommerce_response(res, "Export Product Attribute Terms",
                                                            model_id, common_log_id, template)

            if 'create' not in response_data:
                continue
            for term in response_data['create']:
                woo_term = woo_terms.filtered(lambda x: x.slug == term['slug'])
                woo_term.id = term.get('id', False)

    def find_or_create_woo_attribute(self, attributes_data, instance):
        obj_woo_attribute = self.env['woo.product.attribute.ept']
        odoo_attribute_obj = self.env['product.attribute']

        for attribute in attributes_data:
            woo_attribute = obj_woo_attribute.search([('woo_attribute_id', '=', attribute.get('id')),
                                                      ('woo_instance_id', '=', instance.id),
                                                      ('exported_in_woo', '=', True)], limit=1)
            if woo_attribute:
                continue
            odoo_attribute = odoo_attribute_obj.get_attribute_by_slug(
                attribute,
                auto_create=True,
            )[:1]
            woo_attribute = obj_woo_attribute.search([('attribute_id', '=', odoo_attribute.id),
                                                      ('woo_instance_id', '=', instance.id),
                                                      ('exported_in_woo', '=', False)], limit=1)
            if woo_attribute:
                woo_attribute.write({
                    'woo_attribute_id': attribute.get('id'), 'order_by': attribute.get('order_by'),
                    'slug': attribute.get('slug'), 'exported_in_woo': True,
                    'has_archives': attribute.get('has_archives')
                })
            else:
                obj_woo_attribute.create({
                    'name': attribute.get('name'),
                    'woo_attribute_id': attribute.get('id'),
                    'order_by': attribute.get('order_by'),
                    'slug': attribute.get('slug'),
                    'woo_instance_id': instance.id,
                    'attribute_id': odoo_attribute.id,
                    'exported_in_woo': True,
                    'has_archives': attribute.get('has_archives'),
                })
        return True

    def find_or_create_woo_attribute_term(self, attributes_term_data, instance, woo_attribute):
        obj_woo_attribute_term = self.env['woo.product.attribute.term.ept']
        odoo_attribute_value_obj = self.env['product.attribute.value']

        for attribute_term in attributes_term_data:
            woo_attribute_term = obj_woo_attribute_term.search([
                ('woo_attribute_term_id', '=', attribute_term.get('id')),
                ('exported_in_woo', '=', True),
                ('woo_instance_id', '=', instance.id),
            ], limit=1)
            if woo_attribute_term:
                continue
            odoo_attribute_value = odoo_attribute_value_obj.get_attribute_values_by_slug(
                attribute_term,
                woo_attribute.attribute_id.id,
                auto_create=True,
            )[:1]
            woo_attribute_term = obj_woo_attribute_term.search(
                [('attribute_value_id', '=', odoo_attribute_value.id),
                 ('attribute_id', '=', woo_attribute.attribute_id.id),
                 ('woo_attribute_id', '=', woo_attribute.id), ('woo_instance_id', '=', instance.id),
                 ('exported_in_woo', '=', False)], limit=1)
            if woo_attribute_term:
                woo_attribute_term.write({
                    'woo_attribute_term_id': attribute_term.get('id'),
                    'count': attribute_term.get('count'),
                    'slug': attribute_term.get('slug'),
                    'exported_in_woo': True,
                })
            else:
                obj_woo_attribute_term.create({
                    'name': attribute_term.get('name'),
                    'woo_attribute_term_id': attribute_term.get('id'),
                    'slug': attribute_term.get('slug'),
                    'woo_instance_id': instance.id,
                    'attribute_value_id': odoo_attribute_value.id,
                    'woo_attribute_id': woo_attribute.woo_attribute_id,
                    'attribute_id': woo_attribute.attribute_id.id,
                    'exported_in_woo': True,
                    'count': attribute_term.get('count')})
        return True


class WooProductEpt(models.Model):
    _inherit = "woo.product.product.ept"

    name = fields.Char(translate=False, readonly=True)

    def _update_translations(self):
        for r in self.filtered(lambda r: r.product_id and r.woo_instance_id.woo_lang_id):
            instance_lang = r.woo_instance_id.woo_lang_id
            r.name = r.product_id.with_context(lang=instance_lang.code).name
