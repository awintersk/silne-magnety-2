from odoo import models, fields, api

NUMBER_OF_BULK = 9


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    bulk_discount = fields.Selection(selection='_list_bulk_discounts', default='base_price', required=True)

    @api.model
    def _list_bulk_discounts(self):
        return [('base_price', 'Base Price')] + [(f'bulk_discount_{n}', f'Bulk Discount {n}') for n in range(NUMBER_OF_BULK)]
