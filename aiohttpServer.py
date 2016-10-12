import asyncio
from aiohttp import web, MultiDict
from urllib.parse import urlparse, parse_qsl
import os, sys, logging


class HTTPServer:

    local_path = os.path.dirname(os.path.abspath(sys.argv[0]))

    watcher = None
    ip = None
    port = None

    app = None
    handler = None
    server = None

    def __init__(self, watcher):
        self.watcher = watcher

    def start(self, ip='localhost', port=8080):

        self.ip = ip
        self.port = port

        logging.info("Running HTTP server...")

        self.app = web.Application()
        self.app.router.add_route('GET', '/', self.main_page)
        self.app.router.add_route('GET', '/miners', self.miners)
        self.app.router.add_route('GET', '/dogs', self.dogs)
        self.app.router.add_route('GET', '/register', self.register_miner)
        self.app.router.add_route('GET', '/bind', self.bind_miner)
        self.app.router.add_route('GET', '/unbind', self.unbind_miner)

        self.app.router.add_static('/css', self.local_path + '/www/css', show_index=True)
        self.app.router.add_static('/js', self.local_path + '/www/js', show_index=True)

        self.handler = self.app.make_handler()
        web.run_app(app=self.app, host=self.ip, port=self.port)

        raise Exception('Http server crashed!')

    async def main_page(self, request):
        try:
            with open(self.local_path + "/www/index.html", 'rb') as index:
                return web.Response(headers={"Content-type": "text/html"}, body=index.read())

        except Exception as e:
            logging.critical(e)
            return web.Response(text='Error 404', status=404, charset='utf8')

    async def miners(self, request):
        try:
            return web.json_response(data={"miners": self.watcher._new_miners})
        except Exception as e:
            logging.critical(e)
            return web.Response(text='Error 500', status=500, charset='utf8')

    async def dogs(self, request):

        try:
            response = []
            for dog in self.watcher._dogs:
                response.append(dog['last_data'])
            return web.json_response(data={"dogs": response})

        except Exception as e:
            logging.critical(e)
            return web.Response(text='Error 500', status=500, charset='utf8')

    async def register_miner(self, request):
        name = ''
        try:
            name = MultiDict(parse_qsl(urlparse(request.path_qs).query))["name"]
        except Exception as e:
            return web.Response(text='Error 400', status=400, charset='utf8')

        try:
            registered = await self.watcher.register_miner(name=name, ip=request.transport.get_extra_info('peername')[0])
            if registered:
                return web.Response(text="Miner " + name + " succesfully registered with IP " \
                                    + request.transport.get_extra_info('peername')[0] + "!")
            else:
                return web.Response(text='Error 403', status=403, charset='utf8')

        except Exception as e:
            logging.critical(e)
            return web.Response(text='Error 500', status=500, charset='utf8')

    async def remove_miner(self, request):
        name = ""
        try:
            name = MultiDict(parse_qsl(urlparse(request.path_qs).query))["name"]
        except Exception as e:
            return web.Response(text='Error 400', status=400, charset='utf8')

        try:
            if self.watcher.remove_miner(name=name):
                return web.Response(text="Miner " + name + " succesfully removed!")
            else:
                return web.Response(text='Error 400', status=403, charset='utf8')

        except Exception as e:
            logging.critical(e)
            return web.Response(text='Error 500', status=500, charset='utf8')

    async def bind_miner(self, request):
        name = ""
        dog_ip = None

        try:
            dog_ip = MultiDict(parse_qsl(urlparse(request.path_qs).query))["dogIP"]
        except Exception as e:
            return web.Response(text='Error 400', status=400, charset='utf8')

        try:
            name = MultiDict(parse_qsl(urlparse(request.path_qs).query))["name"]
        except Exception as e:
            return web.Response(text='Error 400', status=400, charset='utf8')

        try:
            try:
                bound = await self.watcher.bind_miner(name, dog_ip=dog_ip)
            except Exception as e:
                return web.Response(text='Error 500', status=500, charset='utf8')

            if bound:
                return web.Response(text="Miner " + name + " successfully bound to dog " + str(dog_ip))
            else:
                return web.Response(text='Error 403', status=403, charset='utf8')

        except Exception as e:
            logging.critical(e)
            return web.Response(text='Error 500', status=500, charset='utf8')

    async def unbind_miner(self, request):
        name = ""
        try:
            name = MultiDict(parse_qsl(urlparse(request.path_qs).query))["name"]
        except Exception as e:
            return web.Response(text='Error 400', status=400, charset='utf8')

        try:
            try:
                unbound = await self.watcher.unbind_miner(name)
            except Exception as e:
                return web.Response(text='Error 500', status=500, charset='utf8')

            if unbound:
                return web.Response(text="Miner " + name + " succesfully unbound form dog!")
            else:
                return web.Response(text='Error 403', status=403, charset='utf8')

        except Exception as e:
            logging.critical(e)
            return web.Response(text='Error 500', status=500, charset='utf8')
