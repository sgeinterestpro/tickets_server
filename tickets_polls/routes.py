"""
filename: routes.py
datetime: 2019-04-19
author: muumlover
"""
from middleware import auth_middleware
from views import *


def setup_routes(app):
    app.router.add_route('*', '/', default_handle)
    app.router.add_route('*', '/ticket_package', TicketHandles.ticket_package)
    app.router.add_route('*', '/ticket_purchase', TicketHandles.ticket_purchase)
    app.router.add_route('*', '/ticket_refund', TicketHandles.ticket_refund)
    app.router.add_route('*', '/ticket_inspect', TicketHandles.ticket_inspect)
    app.router.add_route('*', '/ticket_checked', TicketHandles.ticket_checked)
    app.router.add_route('*', '/ticket_generate', TicketHandles.ticket_generate)
    app.router.add_route('*', '/ticket_usage', TicketHandles.ticket_usage)

    app.router.add_route('*', '/ticket_log', TicketHandles.ticket_log)
    app.router.add_route('*', '/ticket_check_log', TicketHandles.ticket_check_log)

    app.router.add_route('*', '/user_bind', UserHandles.user_bind)
    app.router.add_route('*', '/user_info', UserHandles.user_info)
    app.router.add_route('*', '/user_update', UserHandles.user_update)
    app.router.add_route('*', '/member_add', UserHandles.member_add)
    app.router.add_route('*', '/member_delete', UserHandles.member_delete)
    app.router.add_route('*', '/member_find', UserHandles.member_find)
    app.router.add_route('*', '/member_list', UserHandles.member_list)

    app.router.add_route('*', '/report_export', ReportHandles.report_export)

    app.router.add_route('*', '/web/email_check/{uuid}', WebHandles.email_check, name='email-check')


def setup_middleware(app):
    app.middlewares.append(auth_middleware)
