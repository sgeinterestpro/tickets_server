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

mail_charset = 'utf-8'
mail_host = b'\x73\x6d\x74\x70\x2e\x73\x69\x6e\x61\x2e\x63\x6f\x6d'.decode()
mail_user = b'\x73\x67\x65\x5f\x6e\x6f\x74\x69\x66\x79\x40\x73\x69\x6e\x61\x2e\x63\x6f\x6d'.decode()
mail_pass = b'\x53\x67\x65\x32\x30\x30\x32\x31\x30\x33\x30'.decode()


def setup_email(app):
    app['email'] = EmailSender


class EmailSender:
    @staticmethod
    def send(to_addrs, subject, mail_msg, attachs=None):
        logging.debug((to_addrs, subject, mail_msg, attachs))
        from_addr = mail_user
        if isinstance(to_addrs, str):
            to_addrs = [to_addrs]

        if attachs is None:
            message = MIMEText(mail_msg, _subtype='html', _charset=mail_charset)
        else:
            message = MIMEMultipart()
            msg_text = MIMEText(mail_msg, _subtype='html', _charset=mail_charset)
            message.attach(msg_text)

            if isinstance(attachs, tuple):
                attachs = [attachs]

            for attach_name, attach_io in attachs:
                attachment = MIMEText(attach_io.getvalue(), 'base64', mail_charset)
                attachment['Content-Type'] = Header('application/octet-stream')
                # att_tmp['Content-Disposition'] = f'attachment; filename="{attach_name}"' # 纯英文可用
                attachment.add_header('Content-Disposition', 'attachment', filename=(mail_charset, '', attach_name))
                message.attach(attachment)

        message['X-Mailer'] = 'Microsoft Outlook Express 6.00.2900.2869'
        # message['Subject'] = subject # 纯英文可用
        message['Subject'] = Header(subject, charset=mail_charset).encode()
        message['From'] = from_addr
        message['To'] = ';'.join(to_addrs)

        try:
            with SmtpServer(mail_host, 25) as smtp_server:
                send_errs = smtp_server.sendmail(from_addr, to_addrs, message.as_string())
                if not send_errs:
                    logging.debug('邮件发送成功')
                else:
                    logging.error('邮件发送失败')
                    logging.error(send_errs)
        except Exception as e:
            logging.exception(e)
            raise e


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
    wb = xlwt.Workbook(encoding='utf-8')
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
