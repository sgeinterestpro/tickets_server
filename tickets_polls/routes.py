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


def setup_middleware(app):
    app.middlewares.append(auth_middleware)
