# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    inv_eu_country_group = fields.Many2one('res.country.group', string=_("Country Group EU"),
                                           config_parameter='account.inv_eu_country_group')
    inv_no_eu_country_group = fields.Many2one('res.country.group', string=_("Country Group Outside EU"),
                                              config_parameter='account.inv_no_eu_country_group')
