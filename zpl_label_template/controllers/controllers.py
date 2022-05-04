# -*- coding: utf-8 -*-

import logging

from odoo.http import Controller, route, request
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ZplTemplateController(Controller):

    @route('/zpl_label_template/get_product_zpl_report_id', type='json', auth='user')
    def get_product_zpl_report_id(self, product_int_id: int = None, barcode: str = None):
        product_id = None
        product_env = request.env['product.product']

        if product_int_id:
            product_id = product_env.browse(product_int_id)
        elif barcode:
            product_id = product_env.search([('barcode', '=', barcode)], limit=1)

        if not product_id:
            return None

        template_id = request.env['zpl.label.template'].search([
            ('model_id.model', '=', 'product.product'),
            ('product_category_ids', 'in', product_id.categ_id.ids),
            ('report_id', '!=', False)
        ], limit=1)

        return template_id.report_id.id if template_id else None

    @route([
        '/zpl_label_template/record_list/<model("ir.model"):model_id>',
        '/zpl_label_template/record_list/<string:model_name>'
    ], type='json', auth='user')
    def get_record_list(self, model_id=None, model_name=None, limit=40):
        if not model_id:
            model_id = request.env['ir.model'].search([
                ('model', '=', model_name)
            ], limit=1)

        if not model_id:
            raise UserError('Model not found.')

        _logger.info(model_id.model)

        return request.env[model_id.model].search_read(
            domain=[],
            fields=['display_name', 'name'],
            limit=limit
        )
