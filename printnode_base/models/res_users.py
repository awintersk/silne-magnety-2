# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class User(models.Model):
    """ User entity. Add 'Default Printer' field (no restrictions).
    """
    _inherit = 'res.users'

    printnode_enabled = fields.Boolean(
        string='Auto-print via Direct Print',
        default=False,
    )

    printnode_printer = fields.Many2one(
        'printnode.printer',
        string='Default Printer',
    )

    scales_enabled = fields.Boolean(
        string='Auto-measure with Scales',
        default=False,
    )

    printnode_scales = fields.Many2one(
        'printnode.scales',
        string='Default Scales',
    )

    user_label_printer = fields.Many2one(
        'printnode.printer',
        string='Shipping Label Printer',
    )

    printnode_rule_ids = fields.One2many(
        comodel_name='printnode.rule',
        inverse_name='user_id',
        string='Direct Print Rules',
    )

    # Workstation devices
    printnode_workstation_printer_id = fields.Many2one(
        'printnode.printer',
        string='Default Workstation Printer',
        store=False,
        default=lambda self: self._get_workstation_device('printnode_workstation_printer_id')
    )

    printnode_workstation_label_printer_id = fields.Many2one(
        'printnode.printer',
        string='Default Workstation Shipping Label Printer',
        store=False,
        default=lambda self: self._get_workstation_device('printnode_workstation_label_printer_id')
    )

    printnode_workstation_scale_id = fields.Many2one(
        'printnode.scales',
        string='Default Workstation Scales',
        store=False,
        default=lambda self: self._get_workstation_device('printnode_workstation_scale_id')
    )

    def __init__(self, pool, cr):
        # pylint: disable=return-in-init
        # TODO: Investigate!
        """
        Adding access rights on printnode related fields on user form
        """

        readable_fields = [
            'printnode_enabled',
            'printnode_printer',
            'printnode_scales',
            'scales_enabled',
            'user_label_printer',
            'printnode_rule_ids',
            'printnode_workstation_printer_id',
            'printnode_workstation_label_printer_id',
            'printnode_workstation_scale_id',
        ]
        writable_fields = [
            'printnode_enabled',
            'printnode_printer',
            'printnode_scales',
            'scales_enabled',
            'user_label_printer',
            'printnode_workstation_printer_id',
            'printnode_workstation_label_printer_id',
            'printnode_workstation_scale_id',
        ]

        init_res = super().__init__(pool, cr)
        type(self).SELF_READABLE_FIELDS = type(self).SELF_READABLE_FIELDS + readable_fields
        type(self).SELF_WRITEABLE_FIELDS = type(self).SELF_WRITEABLE_FIELDS + writable_fields
        return init_res

    def get_shipping_label_printer(self):
        """
        Printer search sequence:
        1. Default Workstation Printer (User preferences)
        2. Default printer for current user (User Preferences)
        3. Default printer for current company (Settings)
        """
        company = self.env.company

        # There can be printer for the current workstation
        workstation_label_printer_id = self._get_workstation_device(
            'printnode_workstation_label_printer_id')

        printer = workstation_label_printer_id or self.user_label_printer or \
            company.company_label_printer

        if not printer:
            raise UserError(_(
                'Neither on company level, no on user level default label printer '
                'is defined. Please, define it.'
            ))

        return printer

    def get_report_printer(self, report_id):
        """
        Printer search sequence:
        1. Printer from Print Action Button or Print Scenario (if specified, out of this method)
        2. Printer from User Rules (if exists)
        3. Default Workstation Printer (User preferences)
        4. Default printer for current user (User Preferences)
        5. Default printer for current company (Settings)
        """
        self.ensure_one()

        rule = self.printnode_rule_ids.filtered(lambda r: r.report_id.id == report_id)[:1]

        # There can be printer for the current workstation
        workstation_printer_id = self._get_workstation_device('printnode_workstation_printer_id')

        printer = rule.printer_id or workstation_printer_id or \
            self.printnode_printer or self.env.company.printnode_printer
        printer_bin = rule.printer_bin if rule.printer_id else printer.default_printer_bin

        return printer, printer_bin

    def get_scales(self):
        """
        Scales search sequence:
        3. Default Workstation Scales (User preferences)
        4. Default scales for current user (User Preferences)
        5. Default scales for current company (Settings)
        """
        self.ensure_one()

        # There can be scales for the current workstation
        workstation_scales_id = self._get_workstation_device('printnode_workstation_scales_id')

        scales = workstation_scales_id or self.printnode_scales or self.env.company.printnode_scales

        return scales

    def _get_workstation_device(self, device):
        """
        Helper method to get device set for the current workstation
        """
        # Mapping between workstation device attributes and Odoo models
        mapping = {
            'printnode_workstation_printer_id': 'printnode.printer',
            'printnode_workstation_label_printer_id': 'printnode.printer',
            'printnode_workstation_scales_id': 'printnode.scales',
        }

        if device not in mapping:
            return None

        model = mapping[device]
        workstation_device_id = self.env.context.get(device)

        if not workstation_device_id:
            return None

        try:
            workstation_device_id = int(workstation_device_id)
        except ValueError:
            return None

        workstation_device = self.env[model].browse([workstation_device_id])

        return workstation_device.exists()

    @api.model
    def validate_device_id(self, devices):
        """
        Returns name of devices if related record with specified ID exists
        """
        resp = {}

        for field_name, id in devices.items():
            # Assume that by default ID is wrong
            resp[field_name] = False

            id = int(id)
            fields = self.fields_get([field_name])

            field = fields.get(field_name, {})
            model = field.get('relation')

            # Bad field name or field is not relation
            if not model:
                continue

            resp[field_name] = self.env[model].browse([id]).exists().name

        return resp
