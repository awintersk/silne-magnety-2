import time
import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger("WooCommerce")


class WooProcessImportExport(models.TransientModel):
    _inherit = 'woo.process.import.export'

    def execute(self):
        return super(WooProcessImportExport, self.with_context(lang=self.woo_instance_id.woo_lang_id.code)).execute()

    def update_products(self):
        """
        This method is used to update the existing products in woo commerce
        @author: Dipak Gogiya @Emipro Technologies Pvt. Ltd
        Migration done by Haresh Mori @ Emipro on date 19 September 2020 .
        """
        start = time.time()
        woo_instance_obj = self.env['woo.instance.ept']
        common_log_book_obj = self.env['common.log.book.ept']
        woo_product_tmpl_obj = self.env['woo.product.template.ept']

        if not self.woo_basic_detail and not self.woo_is_set_price and not self.woo_is_set_image and not \
                self.woo_publish:
            raise UserError(_('Please Select any one Option for process Update Products'))

        woo_tmpl_ids = self._context.get('active_ids')
        if woo_tmpl_ids and len(woo_tmpl_ids) > 80:
            raise UserError(_("Error\n- System will not update more then 80 Products at a "
                              "time.\n- Please select only 80 product for update."))

        instances = woo_instance_obj.search([('active', '=', True)])
        woo_tmpl_ids = woo_product_tmpl_obj.browse(woo_tmpl_ids)
        for instance in instances:
            woo_templates = woo_tmpl_ids.filtered(lambda x: x.woo_instance_id.id == instance.id and x.exported_in_woo)
            if not woo_templates:
                continue
            common_log_id = common_log_book_obj.woo_create_log_book('export', instance)

            woo_product_tmpl_obj.update_products_in_woo(instance, woo_templates, self.woo_is_set_price,
                                                        self.woo_publish, self.woo_is_set_image, self.woo_basic_detail,
                                                        common_log_id)
            if not common_log_id.log_lines:
                common_log_id.unlink()
        end = time.time()
        _logger.info("Update products in Woocommerce Store in %s seconds.", str(end - start))
        return True
