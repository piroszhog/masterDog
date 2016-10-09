from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading
from urllib.parse import urlparse, parse_qs
import logging
from datetime import datetime
import json

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

    def response200(self, message=None):
        self.wfile.write(bytes(message, "utf8"))
        self.send_response(200)

    def do_GET(self):

        path = urlparse(self.path).path
        params = parse_qs(urlparse(self.path).query)
        print(path)

        if path == "/":
            try:
                print(handlerHelper.watcher.local_path + "/www/index.html")
                with open(handlerHelper.watcher.local_path + "/www/index.html") as index:
                    self.wfile.write(index.read().encode("utf-8"))
                    self.send_response(200)

            except Exception as e:
                self.send_error(404)

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
                    self.send_error(403)

            except Exception as e:
                logging.critical(e)
                self.send_error(500)
                return

        elif path == "/remove":
            name = ""
            try:
                name = params["name"][0]
            except Exception as e:
                self.send_error(400)
                return

            try:
                if handlerHelper.watcher.remove_miner(name=name):
                    self.response200("Miner " + name + " successfully removed!")
                else:
                    self.send_error(403)

            except Exception as e:
                logging.critical(e)
                self.send_error(500)

        elif path == "/bind":
            name = ""
            dog_id = None
            dog_ip = None

            try:
                dog_id = params["dogId"][0]
            except Exception as e:
                try:
                    dog_ip = params["dogIP"][0]
                except Exception as e:
                    self.send_error(400)
                    return

            try:
                name = params["name"][0]
            except Exception as e:
                self.send_error(400)
                return

            try:
                if handlerHelper.watcher.bind_miner(name, dog_id=dog_id, dog_ip=dog_ip):
                    self.response200("Miner " + name + " successfully bind to dog " + str(dog_id))
                else:
                    self.send_error(403)

            except Exception as e:
                logging.critical(e)
                self.send_error(500)

        elif path == "/unbind":
            name = ""
            try:
                name = params["name"][0]

            except Exception as e:
                self.send_error(400)
                return

            try:
                if handlerHelper.watcher.unbind_miner(name):
                    self.response200("Miner " + name + " successfully unbind from dog.")
                else:
                    self.send_error(403)

            except Exception as e:
                logging.critical(e)
                self.send_error(500)

        elif path == "/dogs":
            response = []

            try:
                for connector in handlerHelper.watcher._dog_connectors:
                    response.append(connector.json_from_last_update)
                self.response200(json.dumps({"dogs": response}))

            except Exception as e:
                logging.critical(e)
                self.send_error(500)

        elif path == "/miners":
            try:
                self.response200(json.dumps({"miners": handlerHelper.watcher.all_miners()}))
            except Exception as e:
                logging.critical(e)
                self.send_error(500)

        elif self.path.endswith(".css"):
            try:
                with open(handlerHelper.watcher.local_path + "/www/" + self.path) as stylesheet:
                    self.send_response(200)
                    self.send_header('Content-type', "text/css")
                    self.end_headers()
                    self.wfile.write(stylesheet.read().encode("utf-8"))
                    self.send_response(200)

            except Exception as e:
                self.send_error(404)

        elif self.path.endswith(".js"):
            try:
                with open(handlerHelper.watcher.local_path + "/www/" + self.path) as stylesheet:
                    self.send_response(200)
                    self.send_header('Content-type', "javascript")
                    self.end_headers()
                    self.wfile.write(stylesheet.read().encode("utf-8"))

            except Exception as e:
                self.send_error(404)

        else:
            self.send_error(404)

        return
