# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    delivery_date = fields.Date(string="Delivery date", copy=False)
    narration_top = fields.Text()

    def _post(self, soft=True):
        res = super()._post(soft=soft)
        for move in res.filtered('invoice_date'):
            move.delivery_date = move.invoice_date
        return res
