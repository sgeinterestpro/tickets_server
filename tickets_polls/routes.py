from views import *


def setup_routes(app):
    app.router.add_route('*', '/', default_handle)
    app.router.add_route('*', '/ticket/{ticket_id}', Ticket.ticket)
    app.router.add_get('/ticket_apply', Ticket.apply)
    app.router.add_post('/ticket_used', Ticket.used)
    app.router.add_post('/ticket_delete', Ticket.delete)
