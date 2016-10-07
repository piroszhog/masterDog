from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading
from urllib.parse import urlparse, parse_qs
import logging
from datetime import datetime


class HTTPHandlerHelper:

    watcher = None
    ip = None
    port = None
    server = None

    def set_watcher(self, watcher):
        self.watcher = watcher

    def start_server(self, ip, port):

        self.ip = ip
        self.port = port

        logging.info("Running HTTP server...")

        server_address = (self.ip, self.port)
        self.server = HTTPServer(server_address, HTTPServerHandler)
        thread = threading.Thread(target=self.server.serve_forever)
        thread.daemon = True
        thread.start()

        logging.info("HTTP server started")
        return

handlerHelper = HTTPHandlerHelper()


class HTTPServerHandler(SimpleHTTPRequestHandler):

    def response200(self, message=None, content_type=None):
        if not content_type:
            content_type = 'application/json'

        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(bytes(message, "utf8"))

    def do_GET(self):

        path = urlparse(self.path).path
        params = parse_qs(urlparse(self.path).query)
        print(path)

        if path == "/":
            html = '<html>'
            html += '<head><link rel="stylesheet" href="/style.css"></head>'
            html += '<body>'
            html += '<table class="data-table">'
            html += '<thead><tr><td class="column-header">Farm</td><td class="column-header">IP</td>'
            html += '<td class="column-header">Last alive time</td></tr></thead><tbody>'

            for farm in handlerHelper.watcher.farm_list():
                html += '<tr>'
                html += '<td>' + farm["name"] + '</td>'
                html += '<td>' + farm["ip"] + '</td>'
                html += '<td>' + datetime.strftime(farm["last_alive_time"], "%Y.%m.%d %H:%M") + '</td>'

                html += '</tr>'

            html += '</tbody></table></body></html>'

            self.response200(html, content_type='text/html')

        elif path == "/register":
            name = ""
            try:
                name = params["name"][0]
            except Exception as e:
                self.send_error(400)
                return

            try:
                if handlerHelper.watcher.register_miner(name=name, ip=self.client_address[0]):
                    self.response200("Miner " + name + " succesfully registered with IP " \
                                        + self.client_address[0] + "!")
                else:
                    self.send_error(400)

            except Exception as e:
                logging.error(e)
                return

        elif path == "/remove":
            name = ""
            try:
                name = params["name"][0]
            except Exception as e:
                self.send_error(400)
                return

            try:
                if handlerHelper.watcher.find_miner(name=name):
                    if handlerHelper.watcher.remove_miner(name=name):
                        self.response200("Miner " + name + " succesfully removed!")
                    else:
                        self.send_error(400)
                else:
                    self.send_error(403)

            except Exception as e:
                logging.error(e)
                return

        elif self.path.endswith(".css"):
            with open(handlerHelper.watcher.local_path + "/" + self.path) as stylesheet:
                self.send_response(200)
                self.send_header('Content-type', "text/css")
                self.end_headers()
                self.wfile.write(stylesheet.read().encode("utf-8"))

        else:
            self.send_error(404)

        return
