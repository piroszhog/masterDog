# -*- coding: utf-8 -*-

import json
from http.client import HTTPConnection
import time
from datetime import datetime

import logging


class DogConnector:

    address = None
    port = None
    stats_url = None

    _http_connection = None
    last_update_response = None
    last_update_datetime = None
    json_from_last_update = None

    def __init__(self, address, port, stats_url):
        try:
            self.address = address
            self.port = port
            self.stats_url = stats_url

        except Exception as e:
            logging.critical(e)

    def connect(self):
        if not self._http_connection:
            try:
                self._http_connection = HTTPConnection(self.address, port=self.port, timeout=10)

            except Exception as e:
                logging.error(datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S") + " - " + str(e))
                self.connect()

        if self.last_update_datetime and (datetime.now() - self.last_update_datetime).total_seconds() < 10:
                time.sleep(10)
        self.last_update_datetime = datetime.now()

    def disconnect(self):
        if self._http_connection:
            self._http_connection.close()
        self._http_connection = None

    def update_stats(self):
        str_response = ""
        try:
            logging.info("Go to http://" + self.address + ":" + str(self.port) + self.stats_url)

            self._http_connection.request("GET", self.stats_url)
            str_response = self._http_connection.getresponse().read().decode('utf-8')

        except Exception as e:
            logging.error(str(e))
            self.disconnect()
            self.connect()

        try:
            self.json_from_last_update = json.loads(str_response)
            self.json_from_last_update["localIP"] = self.address

        except ValueError as e:
            pass
        except Exception as e:
            logging.error(e)
            raise e

        self.last_update_datetime = datetime.now()

    def register_miner(self, name, ip):
        if not name or not ip:
            raise Exception("Name or ip of miner needs for registering it!")

        try:
            url = "/register?name=" + name + "&ip=" + ip
            logging.info("Go to http://" + self.address + ":" + str(self.port) + url)

            self._http_connection.request("GET", url)

        except Exception as e:
            logging.error(str(e))
            self.disconnect()
            self.connect()
            raise e

    def remove_miner(self, name):
        if not name:
            raise Exception("Name of miner needs for removing it!")

        try:
            url = "/remove?name=" + name
            logging.info("Go to http://" + self.address + ":" + str(self.port) + url)

            self._http_connection.request("GET", url)

        except Exception as e:
            logging.error(str(e))
            self.disconnect()
            self.connect()
            raise e
