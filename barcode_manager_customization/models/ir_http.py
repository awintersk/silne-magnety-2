from odoo import models
from odoo.tools.safe_eval import safe_eval


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super(IrHttp, self).session_info()
        parameter_env = self.env['ir.config_parameter'].sudo()
        if self.env.user.has_group('base.group_user'):
            param_key = 'barcode_manager_customization.use_barcode_keypress_event'
            res['use_barcode_keypress_event'] = safe_eval(parameter_env.get_param(param_key, default='False'))
        return res
