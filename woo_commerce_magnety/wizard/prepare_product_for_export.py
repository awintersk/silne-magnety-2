# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import logging
from _collections import OrderedDict
from odoo import api, models, fields, _

_logger = logging.getLogger("WooCommerce")


class PrepareProductForExport(models.TransientModel):
    _inherit = "woo.prepare.product.for.export.ept"

    def prepare_woo_template_layer_vals(self, woo_instance, product_template, product_type):
        data = super(PrepareProductForExport, self).prepare_woo_template_layer_vals(woo_instance, product_template, product_type)
        if len(product_template.product_variant_ids) == 1:
            data.update({
                'woo_product_type': 'simple',
            })
        if self.env["ir.config_parameter"].sudo().get_param("woo_commerce_ept.set_sales_description"):
            data.update({
                "woo_description": product_template.woo_description,
                "woo_short_description": product_template.woo_short_description,
            })
        return data

    @api.model
    def _update_translations(self, variant):
        # Trigger name recompution to except the name from translation
        product_template = variant.product_tmpl_id
        product_template.attribute_line_ids.attribute_id.woo_attribute_line_ids._compute_name()
        product_template.attribute_line_ids.value_ids.woo_attribute_value_ids._compute_name()
        variant.tag_ids.woo_tag_ids._compute_name()

    def create_update_woo_template(self, variant, woo_instance, woo_template_id, woo_category_dict):
        woo_template_id = super(PrepareProductForExport, self).create_update_woo_template(variant, woo_instance, woo_template_id, woo_category_dict)
        product_template = variant.product_tmpl_id
        woo_template = self.env["woo.product.template.ept"].browse(woo_template_id)
        if product_template.categ_ids:
            categories = []
            for categ in product_template.categ_ids:
                self.create_categ_in_woo(categ, woo_instance.id, woo_category_dict)
                woo_categ = self.update_category_info(categ, woo_instance.id)
                categories.append(woo_categ.id)
            woo_template.write(
                {'woo_categ_ids': [(4, c) for c in categories]})

        if variant.tag_ids:
            exported_tags = variant.tag_ids.filtered(lambda r: woo_instance in r.woo_tag_ids.woo_instance_id)
            tag_vals_list = [{
                'name': tag.name,
                'woo_instance_id': woo_instance.id,
                'tag_id': tag.id,
                'slug': tag.name.lower().replace(' ', '-'),
                'exported_in_woo': False,
            } for tag in (variant.tag_ids - exported_tags)]
            if tag_vals_list:
                self.env['woo.tags.ept'].create(tag_vals_list)
            woo_template.write({
                'woo_tag_ids': [(6, 0, [
                    tag.id
                    for tag in variant.tag_ids.woo_tag_ids.filtered(lambda r: r.woo_instance_id == woo_instance)
                ])],
            })

        self._update_translations(variant)
        return woo_template_id

    def prepare_product_for_export(self):
        instance_lang = self.woo_instance_id.woo_lang_id
        return super(PrepareProductForExport, self.with_context(lang=instance_lang.code)).prepare_product_for_export()

    def create_woo_category(self, category_name, instance, parent_id=False, origin_id=False):
        res = self.env["woo.product.categ.ept"].search([
            ('category_id', '=', origin_id.id),
            ('woo_instance_id', '=', instance),
        ], limit=1)
        if not res:
            res = super().create_woo_category(category_name, instance, parent_id)
            res.category_id = origin_id
        return res

    def update_category_info(self, categ_obj, instance_id):
        woo_product_categ = self.env['woo.product.categ.ept']
        woo_categ_id = woo_product_categ.search([('category_id', '=', categ_obj.id),
                                                 ('woo_instance_id', '=', instance_id)], limit=1)
        if not woo_categ_id:
            woo_categ_id = woo_product_categ.create({
                'name': categ_obj.name,
                'woo_instance_id': instance_id,
                'category_id': categ_obj.id,
            })
        else:
            woo_categ_id._compute_name()
        return woo_categ_id

    def create_categ_in_woo(self, category_id, instance, woo_category_dict, ctg_list=None):
        """
        This method is used for find the parent category and its sub category based on category id and
        create or update the category in woo second layer of woo category model.
        :param categ_id: It contain the product category and its type is object
        :param instance: It contain the browsable object of the current instance
        :param ctg_list: It contain the category ids list
        :return: It will return True if the product category successful complete
        """
        if not ctg_list:
            ctg_list = []
        woo_product_categ = self.env['woo.product.categ.ept']
        product_category_obj = self.env['product.category']
        if category_id:
            ctg_list.append(category_id.id)
            self.create_categ_in_woo(category_id.parent_id, instance, woo_category_dict, ctg_list=ctg_list)
        else:
            for categ_id in list(OrderedDict.fromkeys(reversed(ctg_list))):
                if woo_category_dict.get((categ_id, instance)):
                    continue
                list_categ_id = product_category_obj.browse(categ_id)
                parent_category = list_categ_id.parent_id
                woo_product_parent_categ = parent_category and self.search_woo_category(parent_category.name, instance)
                if woo_product_parent_categ:
                    woo_product_category = self.search_woo_category(list_categ_id.name, instance,
                                                                    woo_product_parent_categ)
                    woo_category_dict.update({(categ_id, instance): woo_product_category.id})
                else:
                    woo_product_category = self.search_woo_category(list_categ_id.name, instance)
                    woo_category_dict.update({(categ_id, instance): woo_product_category.id})
                if not woo_product_category:
                    if not parent_category:
                        parent_id = self.create_woo_category(list_categ_id.name, instance, origin_id=list_categ_id)
                        woo_category_dict.update({(categ_id, instance): parent_id.id})
                    else:
                        parent_id = self.search_woo_category(parent_category.name, instance)
                        woo_cat_id = self.create_woo_category(
                            list_categ_id.name,
                            instance,
                            parent_id,
                            origin_id=list_categ_id,
                        )
                        woo_category_dict.update({(categ_id, instance): woo_cat_id.id})
                elif not woo_product_category.parent_id and parent_category:
                    parent_id = self.search_woo_category(parent_category.name, instance, woo_product_parent_categ)
                    if not parent_id:
                        woo_cat_id = self.create_woo_category(
                            list_categ_id.name,
                            instance,
                            parent_id,
                            origin_id=list_categ_id,
                        )
                        woo_category_dict.update({(categ_id, instance): woo_cat_id.id})
                    if not parent_id.parent_id.id == woo_product_category.id and woo_product_categ.instance_id.id == \
                            instance:
                        woo_product_category.write({'parent_id': parent_id.id})
                        woo_category_dict.update({(categ_id, instance): parent_id.id})
        return woo_category_dict
