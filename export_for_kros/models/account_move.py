# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_export_for_kros(self):
        ctx = self._context
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/export_for_kros?ids=%s' % ','.join(str(id) for id in ctx['active_ids']),
            'target': 'self',
        }
