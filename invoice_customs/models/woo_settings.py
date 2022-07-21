# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class WooInstanceEpt(models.Model):
    _inherit = "woo.instance.ept"

    woo_email = fields.Char(string=_('Footer email'))
    woo_phone = fields.Char(string=_('Footer phone'))
    rel_acc_number = fields.Many2one('res.partner.bank', domain="[('partner_id', '=', context.get('company_id'))]")
