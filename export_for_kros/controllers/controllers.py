import io
import xlwt
from datetime import date, datetime
from odoo import api, models
from odoo.exceptions import AccessError
from odoo.http import Controller, route, request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition


class ExportForKros(Controller):

    @route('/web/export_for_kros/', auth='user')
    def index(self, ids, **kw):
        invoices = request.env['account.move'].browse([int(x) for x in ids.split(',')])

        try:
            invoices.check_access_rights('read')
            invoices.check_access_rule('read')
        except AccessError:
            return request.not_found()

        workbook = xlwt.Workbook()
        newsheet = workbook.add_sheet('Hárok1')
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd.mm.yyyy'

        # Partners of invoices
        def vat_county_code(partner):
            country_code = partner.vat and partner.vat[:2]
            if country_code and country_code.isalpha():
                return country_code.upper()
            else:
                return ''

        def vat_serial(partner):
            country_code = partner.vat and partner.vat[:2]
            if country_code and country_code.isalpha():
                return partner.vat[2:]
            elif country_code and not country_code.isalpha():
                return partner.vat
            else:
                return ''

        partner_fields = [
            'name', 'company_registry', 'street', 'zip', 'city', '', 'country_id.name', '', '', '', '', 'vat_payer',
            'email', 'website', 'bank_ids.acc_number', 'bank_ids.bank_id.bic', 'bank_ids.bank_id.name',
            'phone', 'mobile', '', '', 'comment', '', vat_county_code, vat_serial, 'vat_id', '', '', '', '',
            '', '', '', '']

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

        def invoice_vat_county_code(invoice):
            partner = invoice.partner_id
            country_code = partner.vat and partner.vat[:2]
            if country_code and country_code.isalpha():
                return country_code.upper()
            else:
                return ''

        def invoice_vat_serial(invoice):
            partner = invoice.partner_id
            country_code = partner.vat and partner.vat[:2]
            if country_code and country_code.isalpha():
                return partner.vat[2:]
            elif country_code and not country_code.isalpha():
                return partner.vat
            else:
                return ''

        def user_company_invoice_vat_county_code(invoice):
            partner = invoice.user_id.company_id.partner_id
            country_code = partner.vat and partner.vat[:2]
            if country_code and country_code.isalpha():
                return country_code.upper()
            else:
                return ''

        invoice_fields = [
            'name', 'partner_id.name', 'partner_id.company_registry', 'invoice_date', 'invoice_date_due',
            today, 0, 'amount_untaxed', 0, 0, 10, 20, 0, 'amount_tax', 0, 'amount_total', type_of_receipt,
            'OF', 'OFSM', 'partner_id.id', 'partner_id.commercial_partner_id.id', '', '', 'partner_id.street',
            'partner_id.zip', 'partner_id.city', 'partner_id.vat_id', '', '', '', '', '',
            'invoice_line_ids.sale_line_ids.order_id.woo_order_id', 'user_id.name', '', '',
            'invoice_line_ids.sale_line_ids.order_id.payment_gateway_id.name',
            'invoice_line_ids.sale_line_ids.order_id.carrier_id.name', 'currency_id.name', 1, 1, 'amount_total',
            '', '', 'narration', 'partner_id.country_id.name', 'partner_id.country_id.code', invoice_vat_county_code,
            invoice_vat_serial, 'Fio banka (EUR)', '', 'partner_id.country_id.name', 'X', '', '', '',
            user_company_invoice_vat_county_code, 'user_id.company_id.partner_id.vat',
            'user_id.company_id.partner_id.country_id.name', -4, '3 netural',
            'user_id.company_id.partner_id.company_regestry', -4, '', 0, 0, 0, 0, '', '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
        ]
        invoice_line_fields = [
            'name', 'quantity', 'product_uom_id.name', 'price_unit', 'V', 'product_id.standard_price',
            'product_id.lst_price', 'discount', 'K', '', '', '', 604, 1, '', '', 'default_code', '', '', '',
            '(Nedefinované)', '', '(Nedefinované)', '', '(Nedefinované)', 'X', '(Nedefinované)', '', '', 0,
            0, 0, 0, 0, 0, 0, '', 1, '', '', '', '', '', -4, 3, '', '', '', '', '', '', '', 'D2', '', '', '',
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
            pass
        elif isinstance(data, str):
            try:
                res = obj.mapped(data)
                if res:
                    return res[0]
            except KeyError:
                pass
        elif callable(data):
            return data(obj)
        return data
