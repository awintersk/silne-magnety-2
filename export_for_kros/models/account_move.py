# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    company_bank_acc = fields.Many2one(
        'res.partner.bank',
        string='Company Bank Account',
        compute='_compute_company_bank_acc',
    )

    def _compute_company_bank_acc(self):
        res = self.env['res.partner.bank'].read_group(
            domain=[
                ('use_in_kros', '=', True),
                ('partner_id', 'in', self.company_id.partner_id.ids),
                ('currency_id', 'in', self.currency_id.ids),
            ],
            fields=['ids:array_agg(id)', 'partner_id', 'currency_id'],
            groupby=['partner_id', 'currency_id'],
            lazy=False,
        )
        grouped_accs = {
            (acc['partner_id'][0], acc['currency_id'][0]): acc['ids'] and acc['ids'][0] or False
            for acc in res
        }
        for r in self:
            r.company_bank_acc = grouped_accs.get((r.company_id.partner_id.id, r.currency_id.id), False)

    def action_export_for_kros(self):
        ctx = self._context
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/export_for_kros?ids=%s' % ','.join(str(id) for id in ctx['active_ids']),
            'target': 'self',
        }
