from odoo import models


class WooProcessImportExport(models.TransientModel):
    _inherit = 'woo.process.import.export'

    def execute(self):
        return super(WooProcessImportExport, self.with_context(lang=self.woo_instance_id.woo_lang_id.code)).execute()
