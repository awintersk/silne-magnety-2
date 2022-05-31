import io
import xlwt
from datetime import date, datetime
from odoo import api, models
from odoo.http import Controller, route, request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition


class ExportForKros(Controller):

    @route('/web/export_for_kros/', auth='public')
    def index(self, ids, **kw):
        invoices = request.env['account.move'].browse([int(x) for x in ids.split(',')])
        workbook = xlwt.Workbook()
        newsheet = workbook.add_sheet('Hárok1')
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd.mm.yyyy'

        # Partners of invoices
        partner_fields = [
            'name', 'phone', 'street', 'zip', 'city', '', 'country_id.name', '', '', '', '', '', 'vat', 'email',
            'website', 'bank_ids.acc_number', 'bank_ids.bank_id.bic', 'bank_ids.bank_id.name', 'phone',
            'mobile', '', '', 'comment']
        newsheet.write(0, 0, 'R00')
        newsheet.write(0, 1, 'T04')
        i = 1
        for i, partner in enumerate(invoices.mapped('partner_id'), i):
            newsheet.write(i, 0, 'R01')
            for j, field in enumerate(partner_fields, 1):
                newsheet.write(i, j, self.get_value(partner, field))

        # Invoices
        def today(obj):
            return date.today()

        def type_of_receipt(invoice):
            inv_types = {
                'out_invoice': 0,
                'out_refund': 4,
                'in_receipt': 14,
            }
            return inv_types.get(invoice.move_type, 'unknown')

        def invoice_payment_method(invoice):
            # ToDo
            return 'Bankový prevod'

        invoice_fields = [
            'name', 'partner_id.name', '', 'invoice_date', 'invoice_date_due', today, 0, 'amount_tax', 0, 0, 10,
            20, 0, 'Suma DPH vyssia - Amount VAT higher', 'amount_total', type_of_receipt, 'OF', 'OFSM',
            'partner_id.id', 'partner_id.commercial_partner_id.id', '', '', 'partner_id.street', 'partner_id.zip',
            'partner_id.city', '', '', '', '', '', '', 'name', 'invoice_origin', 'user_id.name', '', '',
            invoice_payment_method, 'invoice_line_ids.sale_line_ids.order_id.carrier_id.name', 'currency_id.name',
            1, 1.0, 'amount_total', '', 'narration', 'name', 'partner_id.country_id.name', 'partner_id.country_id.code',
            'partner_id.vat', '/', 'Fio banka (EUR)', '', 'partner_id.country_id.name', 'X', '', 'SWIFT of suppliers',
        ]
        invoice_line_fields = [
            'name', 'quantity', 'product_uom_id.name', 'price_unit', 'V', 'product_id.standard_price',
            'product_id.lst_price', 'discount', 'K'
        ]
        i += 1
        newsheet.write(i, 0, 'R00')
        newsheet.write(i, 1, 'T01')
        for invoice in invoices:
            i += 1
            newsheet.write(i, 0, 'R01')
            for j, field in enumerate(invoice_fields, 1):
                value = self.get_value(invoice, field)
                if isinstance(value, (date, datetime)):
                    newsheet.write(i, j, value, style=date_format)
                else:
                    try:
                        newsheet.write(i, j, value)
                    except Exception as e:
                        pass
            for line in invoice.invoice_line_ids:
                i += 1
                newsheet.write(i, 0, 'R02')
                for j, field in enumerate(invoice_line_fields, 1):
                    newsheet.write(i, j, self.get_value(line, field))

        out = io.BytesIO()
        workbook.save(out)
        out.seek(0)
        filecontent = out.read()
        if not filecontent:
            return request.not_found()
        else:
            filename = 'Zošit.xls'
            return request.make_response(filecontent, [('Content-Type', 'application/octet-stream'),
                                                       ('Content-Disposition', content_disposition(filename))])

    @api.model
    def get_value(self, obj, data):
        """Get value
        :param record obj: odoo record
        :param str or function data: field in format like 'partner_id.name' or func
        """
        if not data:
            return data
        elif isinstance(data, (int, float)):
            return data
        elif isinstance(data, str):
            fds = data.split('.')
            value = obj
            for ff in fds:
                # if field exist where get value else get field like default
                if ff in value:
                    value = value and value[ff] or ''
                elif len(fds) == 1:
                    return data
                else:
                    return value
            return value
        else:
            return data(obj)
