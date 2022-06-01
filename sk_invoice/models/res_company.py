# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class Company(models.Model):
    _inherit = 'res.company'

    company_registry = fields.Char(related='partner_id.company_registry', string=_('Company Registry'), readonly=False, help="IČO")
    vat_payer = fields.Boolean(related='partner_id.vat_payer', string=_("VAT payer"), readonly=False, help="Platca DPH")
    vat = fields.Char(related='partner_id.vat', string=_("Vat ID"), readonly=False, help="IČ DPH")
    vat_id = fields.Char(related='partner_id.vat_id', string=_('Tax ID'), readonly=False, help="DIČ")
    rel_acc_number = fields.Many2one('res.partner.bank', domain="[('partner_id', '=', partner_id)]")
