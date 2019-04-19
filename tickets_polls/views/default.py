from aiohttp import web


async def default_handle(arg):
    text = "Guys, You should not access this page."
    return web.Response(text=text)
