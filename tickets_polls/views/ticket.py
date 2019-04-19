from aiohttp import web


class Ticket:

    def __init__(self):
        pass

    async def ticket(self, request):
        # request['my_private_key'] = "data"
        # name = request.match_info.get('name', "Anonymous")
        # text = "Guys, You should not access this page."
        return web.HTTPFound('/')

    async def apply(self):
        data = {'some': 'data'}
        return web.json_response(data)

    async def used(self):
        return web.Response(text="Hello, world")

    async def delete(self):
        return web.Response(text="Hello, world")
