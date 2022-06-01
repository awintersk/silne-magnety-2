# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResPartnerInit(models.Model):
    _inherit = 'res.partner'

    vat_payer = fields.Boolean(string=_("VAT payer"))
    vat = fields.Char(string=_('Vat ID'), help="The Tax Identification Number (IČ DPH). Complete it if the contact is subjected to government taxes. Used in some legal statements.")
    vat_id = fields.Char(string=_('Tax ID'), help="DIČ")
    company_registry = fields.Char(string=_('Company Registry'), help="IČO")




