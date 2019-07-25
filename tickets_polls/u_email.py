"""
filename: u_email.py
datetime: 2019-07-08
author: muumlover
"""
import logging
import smtplib
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import dns.resolver

mail_charset = None
server_email = 'system@sge-tech.com'


def setup_email(app):
    app['email'] = EmailSender

    global mail_charset
    mail_charset = app['config']['email']['charset']

    global mail_servers
    mail_servers = app['config']['email']['servers']


class EmailSender:
    @staticmethod
    async def send(to_emails, subject, mail_msg, attachs=None):
        logging.debug(('邮件收件人：', to_emails))
        logging.debug((to_emails, subject, mail_msg, attachs))
        from_email = server_email
        if isinstance(to_emails, str):
            to_emails = [to_emails]

        if attachs is None:
            message = MIMEText(mail_msg, _subtype='html', _charset=mail_charset)
        else:
            message = MIMEMultipart()
            msg_text = MIMEText(mail_msg, _subtype='html', _charset=mail_charset)
            message.attach(msg_text)

            if isinstance(attachs, tuple):
                attachs = [attachs]

            for attach_name, attach_io in attachs:
                attachment = MIMEApplication(attach_io.getvalue(),
                                             'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                # att_tmp['Content-Disposition'] = f'attachment; filename="{attach_name}"' # 纯英文可用
                attachment.add_header('Content-Disposition', 'attachment', filename=(mail_charset, '', attach_name))
                message.attach(attachment)

        # message['Subject'] = subject # 纯英文可用
        message['Subject'] = Header(subject, charset=mail_charset).encode()
        message['From'] = f'Ticket System<{from_email}>'
        message['To'] = ';'.join(to_emails)
        # message['Bcc'] = ";".join([from_addr])

        try:
            to_domain_set = set([to_email.split('@')[1] for to_email in to_emails])
            for to_domain in to_domain_set:
                try:
                    with SmtpServer(to_domain) as smtp_server:
                        send_errs = smtp_server.send_message(message, from_email, to_emails)
                        if not send_errs:
                            logging.debug(f'邮件投递到{to_domain}成功')
                        else:
                            logging.error(f'邮件投递到{to_domain}失败')
                            logging.error(send_errs)
                except dns.resolver.NoAnswer:
                    logging.error(f'服务器 {to_domain} MX 记录解析失败')
        except smtplib.SMTPDataError as err:
            logging.error(f'邮件投递失败')
            logging.exception(err)
            raise smtplib.SMTPDataError(err.smtp_code, err.smtp_error)
        except Exception as err:
            logging.error(f'邮件投递失败')
            logging.exception(err)
            raise smtplib.SMTPDataError(-1, b'Unknown Error')


class SmtpServer:
    def __init__(self, domain):
        mx = dns.resolver.query(domain, 'MX')
        server_addr = mx[0].exchange.to_text()
        _server = smtplib.SMTP(server_addr)
        self.server = _server

    def __enter__(self):
        return self.server

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.server.quit()


if __name__ == '__main__':
    from sys import stdout

    logging.basicConfig(
        format='%(levelname)s: %(asctime)s [%(filename)s:%(lineno)d] %(message)s',
        level=logging.NOTSET,
        stream=stdout)

    import pathlib
    from config import load_config

    conf = load_config(str(pathlib.Path('..') / 'config' / 'polls.yaml'))
    mail_charset = conf['email']['charset']
    mail_servers = conf['email']['servers']

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
