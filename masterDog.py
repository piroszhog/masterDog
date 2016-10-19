import os, sys, logging, coloredlogs
from logging.handlers import RotatingFileHandler

import asyncio
import aiohttp
from aiohttpServer import HTTPServer

from datetime import datetime
import json


class MasterDog:

    local_path = os.path.dirname(os.path.abspath(sys.argv[0]))

    event_loop = asyncio.get_event_loop()
    client = aiohttp.ClientSession(loop=event_loop)
    server = None

    # {"name": miner_name, "ip": miner_ip, "dog_ip": ip_address}
    _new_miners = []
    # Objects from state.json of MiningWatchDog
    _dogs = []

    def __init__(self, config_path):

        coloredlogs.install(level='DEBUG')
        logging.getLogger('').addHandler(RotatingFileHandler(
                    os.path.dirname(os.path.abspath(sys.argv[0])) + '/masterDog.log', maxBytes=(1048576*5), backupCount=7))

        self.config_path = config_path
        self.remove_miners_after = self._get_var("REMOVE_MINERS_AFTER")
        if not self.remove_miners_after:
            self.remove_miners_after = 600

        dog_id = 0
        dog_ip = self._get_var("WATCHDOG_IP_" + str(dog_id), is_required=True)

        while dog_ip:
            dog_port = self._get_var("WATCHDOG_PORT_" + str(dog_id), is_required=True)
            new_dog = {'ip': dog_ip,
                       'port': dog_port,
                        'stats_url': 'http://' + dog_ip + ':' + str(dog_port) + '/state',
                        'last_update_response': None,
                        'last_update_datetime': None,
                        'last_data': None}
            self._dogs.append(new_dog)
            dog_id += 1
            dog_ip = self._get_var("WATCHDOG_IP_" + str(dog_id))

        asyncio.ensure_future(self.update_stats())
        asyncio.ensure_future(self.remove_old_miners())

        self.server = HTTPServer(self)
        self.server.start(self._get_var("SERVER_IP", is_required=True),
                          self._get_var("SERVER_PORT", is_required=True))


    def _get_var(self, var, is_required=False):
        try:
            file = open(self.config_path, 'r')
            for line in file:
                if not line.count('#') and line.count('='):
                    cfgvars = line.split('=')
                    varname = cfgvars[0].strip()
                    value = cfgvars[1].strip()
                    if value in ('True','False'):
                        value = value == 'True'
                    elif not value.count('"'):
                        value = int(value)
                    else:
                        value = value.replace('"','')
                    if var == varname:
                        file.close()
                        return value
            file.close()

        except Exception as e:
            raise e

        if not is_required:
            logging.info("Variable " + str(var) + " not found in config file!")
            return None
        else:
            raise Exception("Variable " + str(var) + " must be in config file!")

    async def update_stats(self):
        while True:
            for dog in self._dogs:
                try:
                    logging.info("Go to " + dog['stats_url'])
                    async with self.client.get(dog['stats_url']) as response:
                        assert response.status == 200
                        bytes_response = await response.read()

                        dog['last_update_datetime'] = datetime.now().isoformat()
                        dog['last_update_response'] = bytes_response.decode('utf8')

                except Exception as e:
                    logging.critical("Can not connect to dog " + dog['ip'] + "!")
                    continue

                try:
                    dog['last_data'] = json.loads(dog['last_update_response'])
                    dog['last_data']['localIP'] = dog['ip']

                except ValueError as e:
                    pass
                except Exception as e:
                    logging.error(e)
                    return False

            await asyncio.sleep(1)

    async def register_miner(self, name, ip):
        if not name or not ip:
            raise Exception("Name or id of miner needs for registering it!")

        new_miner = True

        # Try to find in dogs
        try:
            for dog in self._dogs:
                if dog['last_data'] and dog['last_data']['miners']:
                    for miner in dog['last_data']['miners']:
                        if miner["host"] == ip and miner["name"] != name:
                            try:
                                await self.unbind_miner(miner["name"], remove_after=True)
                            except Exception as e:
                                return False

                        if miner["name"] == name and miner["host"] != ip:
                            try:
                                new_miner = False
                                await self.bind_miner(name, dog['ip'], miner_ip=ip)

                            except Exception as e:
                                logging.error("Can not register miner " + name + "!")
                                return False

        except Exception as e:
            logging.error(e)

        # Try to find in new miners
        if new_miner:
            for miner in self._new_miners:
                if miner["name"] == name:
                    miner["host"] = ip
                    new_miner = False
                if not (miner["name"] == name) and miner["ip"] == ip:
                    self._new_miners.remove(miner)

        if new_miner:
            self._new_miners.append({"name": name,
                                     "ip": ip,
                                     "dog_ip": None,
                                     "registration_time": datetime.now().isoformat()})

        return True

    async def bind_miner(self, name, dog_ip, miner_ip=None):
        if not name or not dog_ip:
            raise Exception("Name of miner needs to bind it!")

        miner = None
        for one_miner in self._new_miners:
            if one_miner['name'] == name:
                miner = one_miner
                if not miner_ip:
                    miner_ip = miner['ip']
                break

        if not miner_ip and not miner:
            logging.error("Can not bind miner " + name + ", because miner is not registered!")
            return False

        for dog in self._dogs:
            if dog["ip"] == dog_ip:
                try:
                    url = 'http://' + dog['ip'] + ":" + str(dog['port']) + "/register?name=" + name + "&ip=" + miner_ip
                    logging.info("Go to " + url)
                    async with self.client.get(url) as response:
                        assert response.status == 200
                        await response.read()

                except Exception as e:
                    logging.critical(e)
                    raise e

                if miner:
                    self._new_miners.remove(miner)
                return True

        logging.error("Can not bind miner " + name + "! Watchdog " + dog_ip + " not found!")
        return False

    async def unbind_miner(self, name, remove_after=False):

        for dog in self._dogs:
            if dog['last_data'] and dog['last_data']['miners']:
                for miner in dog['last_data']['miners']:
                    if name == miner['name']:
                        try:
                            url = 'http://' + dog['ip'] + ":" + str(dog['port']) + '/remove?name=' + name
                            async with self.client.get(url) as response:
                                assert response.status == 200
                                await response.read()

                        except Exception as e:
                            logging.critical(e)
                            raise e

                        if not remove_after:
                            self._new_miners.append({"name": name, "ip": miner["host"], "dog_ip": None})
                        return True

        logging.error("Can not unbind miner, because it's not under the dog.")
        return False

    def unregister_miner(self, name):
        for miner in self._new_miners:
            if miner['name'] == name:
                self._new_miners.remove(miner)
                return True

        logging.error("Can not remove miner! Miner " + name + " not found.")
        return False

    async def remove_old_miners(self):
        while True:
            for miner in self._new_miners:
                if (miner["registration_time"] - datetime.now().isoformat()).total_seconds() > self.remove_miners_after:
                    print("REMOVE!!!!!!")
                    self.unregister_miner(miner["name"])

            await asyncio.sleep(60)


master = MasterDog(os.path.dirname(os.path.abspath(sys.argv[0])) + '/masterDog.conf')