'''
filename: u_email.py
datetime: 2019-07-08
author: muumlover
'''

import smtplib
from email.header import Header
from email.mime.text import MIMEText

mail_host = 'smtp.sina.com'
mail_user = 'sge_notify@sina.com'
mail_pass = b'\x53\x67\x65\x32\x30\x30\x32\x31\x30\x33\x30'.decode()


class SmtpServer:
    def __init__(self, host, port):
        _server = smtplib.SMTP(host, port)
        _server.login(mail_user, mail_pass)
        self.server = _server

    def __enter__(self):
        return self.server

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.server.close()


def send_email(receivers, subject, mail_msg):
    message = MIMEText(mail_msg, 'html', 'utf-8')
    message['From'] = Header(mail_user)
    message['To'] = Header(receivers)
    message['Subject'] = Header(subject, 'utf-8')
    with SmtpServer(mail_host, 25) as smtp_server:
        smtp_server.sendmail(mail_user, receivers, message.as_string())
        print('邮件发送成功')


send_email('wangsen@primeton.com', '正式测试邮件',
           '正式测试邮件<a target="_blank" href="https://www.cnblogs.com/zixuan-zhang/p/3402825.html" h="ID=SERP,5251.1">Python 用IMAP接收邮件 - viczzx - 博客园</a>')
