"""
filename: routes.py
datetime: 2019-04-19
author: muumlover
"""
from aiohttp.abc import Application

from middleware import auth_middleware
from views import *


def setup_routes(app: Application) -> None:
    app.router.add_route('*', '/', default_handle)
    app.router.add_route('*', '/ticket_package', TicketHandles.ticket_package)
    app.router.add_route('*', '/ticket_purchase', TicketHandles.ticket_purchase)
    app.router.add_route('*', '/ticket_refund', TicketHandles.ticket_refund)
    app.router.add_route('*', '/ticket_inspect', TicketHandles.ticket_inspect)
    app.router.add_route('*', '/ticket_checked', TicketHandles.ticket_checked)
    app.router.add_route('*', '/ticket_generate', TicketHandles.ticket_generate)
    app.router.add_route('*', '/ticket_usage', TicketHandles.ticket_usage)
    app.router.add_route('*', '/ticket_batch', TicketHandles.ticket_batch)

    app.router.add_route('*', '/ticket_sign_in', TicketHandles.ticket_sign_in)

    app.router.add_route('*', '/ticket_log', TicketHandles.ticket_log)
    app.router.add_route('*', '/ticket_check_log', TicketHandles.ticket_check_log)
    app.router.add_route('*', '/ticket_check_count', TicketHandles.ticket_check_count)

    app.router.add_route('*', '/message_list', MessageHandles.message_list)
    app.router.add_route('*', '/message_count', MessageHandles.message_count)
    app.router.add_route('*', '/message_action', MessageHandles.message_action)

    app.router.add_route('*', '/user_bind', UserHandles.user_bind)
    app.router.add_route('*', '/user_info', UserHandles.user_info)
    app.router.add_route('*', '/user_update', UserHandles.user_update)
    app.router.add_route('*', '/member_add', UserHandles.member_add)
    # app.router.add_route('*', '/member_delete', UserHandles.member_delete)
    app.router.add_route('*', '/member_delete', UserHandles.member_delete_temp)
    app.router.add_route('*', '/member_suspend', UserHandles.member_suspend)
    app.router.add_route('*', '/member_resume', UserHandles.member_resume)
    app.router.add_route('*', '/member_edit', UserHandles.member_edit)
    app.router.add_route('*', '/member_find', UserHandles.member_find)
    app.router.add_route('*', '/member_list', UserHandles.member_list)

    app.router.add_route('*', '/report_list', ReportHandles.report_list)
    app.router.add_route('*', '/report_export', ReportHandles.report_export)

    app.router.add_route('*', '/auth/weixin/login', WeiXinHandles.login)

    app.router.add_route('*', '/web/rsa_pub_key', SystemHandles.rsa_pub_key)

    app.router.add_route('*', '/web/email_check/{uuid}', WebHandles.email_check, name='email-check')


def setup_middleware(app: Application) -> None:
    app.middlewares.append(auth_middleware)
