# -*- coding: UTF-8 -*-

################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2019 SmartTek (<https://smartteksas.com/>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from io import BytesIO
from base64 import encodebytes
from typing import List, Optional
from xlsxwriter.format import Format
from odoo.tools.misc import xlsxwriter


class XLSXContentManager:
    __output: Optional[BytesIO]
    __worksheet_map: dict = {}
    workbook: Optional[xlsxwriter.Workbook]
    worksheet = None
    content: bytes = b''
    is_open: bool = False
    body_row: int = 1
    headers: List[str] = []
    header_format: Optional[Format] = None
    body_format: Optional[Format] = None

    def __init__(self, headers: List[str]):
        self.headers = headers

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.save()

    def open(self):
        self.__output = BytesIO()
        self.workbook = xlsxwriter.Workbook(self.__output, {'in_memory': True})
        self.is_open = True

    def save(self) -> None:
        if self.is_open:
            self.workbook.close()
            self.content = self.__content()
            self.__output.close()
            self.is_open = False

        self.body_row = 1
        self.workbook = None
        self.worksheet = None
        self.body_format = None
        self.header_format = None
        self.__output = None
        self.__worksheet_map = {}

    def __content(self) -> bytes:
        self.__output.seek(0)
        return encodebytes(self.__output.getvalue())

    def create_switch_worksheet(self, name: str):
        if name in self.__worksheet_map:
            self.worksheet = self.__worksheet_map[name]
        else:
            self.worksheet = self.workbook.add_worksheet(name)
            self.__worksheet_map[name] = self.worksheet
        return self.worksheet

    def write_headers(self):
        column_width = len(max(filter(lambda item: len(item), self.headers)))
        self.worksheet.set_column('A:Z', column_width)
        for col, title in enumerate(self.headers):
            self.worksheet.write_string(0, col, title, self.header_format)

    def write_dict(self, data: dict):
        for key, item in data.items():
            if key not in self.headers:
                raise KeyError(key)
            col = self.headers.index(key)
            if not item and type(item) not in (float, int):
                item = ''
            self.worksheet.write(self.body_row, col, item, self.body_format)
        self.body_row += 1
