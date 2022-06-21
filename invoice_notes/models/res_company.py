# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class Company(models.Model):
    _inherit = 'res.company'

    inv_message_1 = fields.Char(string=_("Invoice Message #1"), translate=True)
    inv_message_2 = fields.Char(string=_("Invoice Message #2"), translate=True)
