import os
import unittest

import openpyxl

from test_ticket.test_base import TestBase, async_test, date_convert
from u_report import ReportBase, ReportUsedDay, ReportUsedMonth, ReportUsedDtl


class Report(TestBase):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        ReportBase.db = self.db
        ReportBase.sender = self.sender
        ReportBase.sport_map = self.config.get('ticket', {}).get('sport', {})
        ReportBase.state_map = self.config.get('ticket', {}).get('state', {})

    async def base_report_test(self, report, start_data, end_data, name):
        eq = self.assertEqual
        filename, content = await report(start_data, end_data).get_attachs()
        with open(filename, 'wb') as xls:
            xls.write(content.getvalue())
        eq(filename, name)
        eq(os.path.exists(filename), True)
        return filename

    @async_test
    async def test_ReportUsedDay(self):
        eq = self.assertEqual
        start_data = '2019-01-01'
        end_data = '2019-12-31'
        start_day = date_convert(start_data, "%Y.%m.%d")
        end_day = date_convert(end_data, "%Y.%m.%d")
        filename = await self.base_report_test(
            ReportUsedDay,
            start_data, end_data,
            f'票券使用统计日报表_{start_day}-{end_day}.xlsx')
        tb_tmp = openpyxl.load_workbook(filename)
        # tb_tmp.active.title
        eq(tb_tmp.worksheets[0].title, '统计')
        # os.remove(filename)

    @async_test
    async def test_ReportUsedMonth(self):
        start_data = '2019-01-01'
        end_data = '2019-12-31'
        start_day = date_convert(start_data, "%Y.%m")
        end_day = date_convert(end_data, "%Y.%m")
        filename = await self.base_report_test(
            ReportUsedMonth,
            start_data, end_data,
            f'票券使用统计月度报表_{start_day}-{end_day}.xlsx')
        # os.remove(filename)

    @async_test
    async def test_ReportUsedDtl(self):
        data = '2019-01-01'
        day = date_convert(data, "%Y.%m.%d")
        filename = await self.base_report_test(
            ReportUsedDtl,
            data, None,
            f'领用登记明细表_{day}.xlsx')
        # os.remove(filename)


if __name__ == '__main__':
    unittest.main()
