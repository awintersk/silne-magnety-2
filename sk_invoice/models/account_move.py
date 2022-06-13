# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    delivery_date = fields.Date(string="Delivery date", copy=False)
    narration_top = fields.Text()
