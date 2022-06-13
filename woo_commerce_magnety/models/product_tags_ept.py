################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2019 SmartTek (<https://smartteksas.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo import _, api, models, fields
from odoo.exceptions import UserError


class WooTagsEpt(models.Model):
    _inherit = 'woo.tags.ept'

    tag_id = fields.Many2one('product.template.tag', string='Tag')
    name = fields.Char(compute='_compute_name', store=True, translate=False)
    woo_product_template_ids = fields.Many2many(
        'woo.product.template.ept',
        'woo_template_tags_rel',
        'woo_tag_id',
        'woo_template_id',
        "Woo Products",
    )

    def _compute_name(self):
        for r in self.filtered(lambda r: r.tag_id and r.woo_instance_id.woo_lang_id):
            instance_lang = r.woo_instance_id.woo_lang_id
            r.name = r.tag_id.with_context(lang=instance_lang.code).name

    def woo_sync_product_tags(self, instance, woo_common_log_id):
        """
        This method is used for collecting the tags information and also sync the tags into woo commerce in odoo
        :param instance: It is the browsable object of the woo instance
        :param woo_common_log_id: It contain the browsable object of the common log book ept model
        :return: return True if the process of tags is successful complete
        """
        common_log_line_obj = self.env["common.log.lines.ept"]
        model_id = common_log_line_obj.get_model_id("woo.tags.ept")
        wc_api = instance.woo_connect()
        try:
            res = wc_api.get("products/tags", params={"per_page": 100})
        except Exception as error:
            raise UserError(_("Something went wrong while importing Tags.\n\nPlease Check your Connection and "
                              "Instance Configuration.\n\n" + str(error)))

        results = self.check_woocommerce_response(res, "Get Product Tags", model_id, woo_common_log_id)
        if not isinstance(results, list):
            return False
        total_pages = res.headers.get('x-wp-totalpages', 0) or 1
        if int(total_pages) >= 2:
            for page in range(2, int(total_pages) + 1):
                results += self.woo_import_all_tags(wc_api, page, woo_common_log_id, model_id)

        for res in results:
            if not isinstance(res, dict):
                continue
            self = self.with_context(lang=instance.woo_lang_id.code)
            tag_id = res.get('id')
            name = res.get('name')
            description = res.get('description')
            slug = res.get('slug')
            woo_tag = self.search([
                "&", ('woo_instance_id', '=', instance.id),
                "|", ('woo_tag_id', '=', tag_id),
                     ('slug', '=', slug)
            ], limit=1)
            if woo_tag:
                woo_tag.write({'woo_tag_id': tag_id, 'name': name, 'description': description,
                               'slug': slug, 'exported_in_woo': True})
            else:
                woo_tag = self.create({
                    'woo_tag_id': tag_id, 'name': name, 'description': description,
                    'slug': slug, 'woo_instance_id': instance.id, 'exported_in_woo': True,
                })

            lang = instance.woo_lang_id.code
            self = self.with_context(lang=lang)
            if woo_tag.tag_id:
                woo_tag.tag_id.with_context(lang=lang).write({'name': name})
            else:
                product_tag = self.env['woo.tags.ept'].search([
                    ('slug', '=', woo_tag.slug),
                    ('tag_id', '!=', False),
                ], limit=1).tag_id
                if not product_tag:
                    # if self.env['product.template.tag'].search([('name', '=', name)], limit=1):
                        # TODO: raise UserError(_("Tag with name '%s' (%s) already exists.") % name, woo_tag.slug)
                    if not self.env['product.template.tag'].search([('name', '=', name)], limit=1):
                        product_tag = self.env['product.template.tag'].create({'name': name})
                woo_tag.tag_id = product_tag

        return True

    def update_product_template_tags(self):
        WooTag = self.env['woo.tags.ept']
        Tag = self.env['product.template.tag']

        for woo_tag in self:
            lang = woo_tag.woo_instance_id.woo_lang_id.code
            if woo_tag.tag_id:
                woo_tag.tag_id.with_context(lang=lang).name = woo_tag.name
                return

            product_tag = WooTag.search([
                ('slug', '=', woo_tag.slug),
                ('tag_id', '!=', False),
            ], limit=1).tag_id
            if product_tag:
                product_tag.with_context(lang=lang).name = woo_tag.name
            else:
                if Tag.with_context(lang=lang).search([('name', '=', woo_tag.name)], limit=1):
                    # TODO: raise UserError(_("Tag with name '%s' (%s) already exists.") % name, woo_tag.slug)
                    continue
                product_tag = Tag.with_context(lang=lang).create({'name': woo_tag.name})
