"""
filename: routes.py
datetime: 2019-04-19
author: muumlover
"""
from middleware import auth_middleware
from views import *


def setup_routes(app):
    app.router.add_route('*', '/', default_handle)
    app.router.add_route('*', '/ticket', TicketRouter)
    app.router.add_route('*', '/ticket/{ticket_id}', TicketRouter)
    app.router.add_route('*', '/ticket_package', TicketHandles.ticket_package)
    app.router.add_route('*', '/ticket_purchase', TicketHandles.ticket_purchase)
    app.router.add_route('*', '/ticket_refund', TicketHandles.ticket_refund)
    app.router.add_route('*', '/ticket_inspect', TicketHandles.ticket_inspect)
    app.router.add_route('*', '/ticket_checked', TicketHandles.ticket_checked)
    app.router.add_route('*', '/ticket_generate', TicketHandles.ticket_generate)
    app.router.add_route('*', '/ticket_usage', TicketHandles.ticket_usage)
    app.router.add_route('*', '/ticket_log', TicketHandles.ticket_log)
    app.router.add_route('*', '/user_info', UserHandles.user_info)
    app.router.add_route('*', '/user_bind', UserHandles.user_bind)

    app.router.add_route('*', '/web/email_check/{uuid}', WebHandles.email_check, name='email-check')


def setup_middleware(app):
    app.middlewares.append(auth_middleware)
