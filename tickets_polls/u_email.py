"""
filename: u_email.py
datetime: 2019-07-08
author: muumlover
"""
import logging
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

mail_host = b'\x73\x6d\x74\x70\x2e\x73\x69\x6e\x61\x2e\x63\x6f\x6d'.decode()
mail_user = b'\x73\x67\x65\x5f\x6e\x6f\x74\x69\x66\x79\x40\x73\x69\x6e\x61\x2e\x63\x6f\x6d'.decode()
mail_pass = b'\x53\x67\x65\x32\x30\x30\x32\x31\x30\x33\x30'.decode()


def setup_email(app):
    app['email'] = EmailSender


class EmailSender:
    @staticmethod
    def send(to_addrs, subject, mail_msg, attachs):
        logging.debug((to_addrs, subject, mail_msg, attachs))
        from_addr = mail_user
        if isinstance(to_addrs, str):
            to_addrs = [to_addrs]

        if attachs is None:
            message = MIMEText(mail_msg, _subtype='html', _charset='gbk')
        else:
            message = MIMEMultipart()
            msg_text = MIMEText(mail_msg, _subtype='html', _charset='gbk')
            message.attach(msg_text)

            if isinstance(attachs, tuple):
                attachs = [attachs]

            for attach_name, attach_io in attachs:
                att_tmp = MIMEText(attach_io.getvalue(), 'base64', 'utf-8')
                att_tmp['Content-Type'] = 'application/octet-stream'
                att_tmp['Content-Disposition'] = f'attachment; filename="{attach_name}"'
                message.attach(att_tmp)

        message.add_header('X-Mailer', 'Microsoft Outlook Express 6.00.2900.2869')
        message['From'] = Header(from_addr)
        message['To'] = Header(','.join(to_addrs))
        message['Subject'] = Header(subject, 'gbk')

        try:
            with SmtpServer(mail_host, 25) as smtp_server:
                smtp_server.sendmail(from_addr, to_addrs, message.as_string())
                logging.debug('邮件发送成功')
        except Exception as e:
            logging.exception(e)


class SmtpServer:
    def __init__(self, host, port):
        _server = smtplib.SMTP(host, port)
        _server.login(mail_user, mail_pass)
        self.server = _server

    def __enter__(self):
        return self.server

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.server.close()


if __name__ == '__main__':
    from sys import stdout

    logging.basicConfig(
        format='%(levelname)s: %(asctime)s [%(filename)s:%(lineno)d] %(message)s',
        level=logging.NOTSET,
        stream=stdout)

    import xlwt
    from io import BytesIO

    # 创建一个文件对象
    wb = xlwt.Workbook(encoding='utf8')
    # 创建一个sheet对象
    sheet = wb.add_sheet('order-sheet')

    style_heading = xlwt.easyxf("""
                font:
                    name Arial,
                    colour_index white,
                    bold on,
                    height 0xA0;
                align:
                    wrap off,
                    vert center,
                    horiz center;
                pattern:
                    pattern solid,
                    fore-colour 0x19;
                borders:
                    left THIN,
                    right THIN,
                    top THIN,
                    bottom THIN;
                """)

    # 写入文件标题
    sheet.write(0, 0, '申请编号', style_heading)
    sheet.write(0, 1, '客户名称', style_heading)
    sheet.write(0, 2, '联系方式', style_heading)
    sheet.write(0, 3, '身份证号码', style_heading)
    sheet.write(0, 4, '办理日期', style_heading)
    sheet.write(0, 5, '处理人', style_heading)
    sheet.write(0, 6, '处理状态', style_heading)
    sheet.write(0, 7, '处理时间', style_heading)

    # 写出到IO
    output = BytesIO()
    wb.save(output)

    EmailSender.send(
        'wangsen@primeton.com', '数据导出报表',
        '您好：请在这里<a class="follow-nickName" href="https://me.csdn.net/offbeatmine" target="_blank">下载报表</a>',
        ('Download.xlsx', output))
    # EmailSender.send_attach(
    #     'wangsen@primeton.com', '数据导出报表',
    #     '您好：请在这里<a class="follow-nickName" href="https://me.csdn.net/offbeatmine" target="_blank">下载报表</a>')
