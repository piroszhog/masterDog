from httpServer import handlerHelper
import os, sys, logging, coloredlogs
from logging.handlers import RotatingFileHandler
from dogConnector import DogConnector
from datetime import datetime


class MasterDog:

    local_path = os.path.dirname(os.path.abspath(sys.argv[0]))

    _dog_connectors = []

    # {"name": miner_name, "ip": miner_ip, "dog_id": id (starts from 1)}
    _all_miners = []

    def __init__(self, config_path):

        coloredlogs.install(level='DEBUG')
        logging.getLogger('').addHandler(RotatingFileHandler(
                    os.path.dirname(os.path.abspath(sys.argv[0])) + '/masterDog.log', maxBytes=(1048576*5), backupCount=7))

        self.config_path = config_path

        handlerHelper.set_watcher(self)
        handlerHelper.start_server(self._get_var("SERVER_IP", is_required=True),
                                       self._get_var("SERVER_PORT", is_required=True))

        id = 0
        dog = self._get_var("WATCHDOG_IP_" + str(id), is_required=True)

        while dog:
            self._dog_connectors.append(DogConnector(dog, 32000, "/state"))
            id += 1
            dog = self._get_var("WATCHDOG_IP_" + str(id))

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

    def update_stats(self):
        for connector in self._dog_connectors:
            connector.update_stats()

    def register_miner(self, name, ip):
        if not name or not ip:
            raise Exception("Name or id of miner needs for registering it!")

        miner_found = False
        for miner in self._all_miners:

            if miner["ip"] == ip and not (miner["name"] == name):
                miner["ip"] = None

            if miner["name"] == name and not miner["dog_id"]:
                miner["ip"] = ip
                miner_found = True

            if miner["name"] == name and miner["dog_id"]:
                try:
                    self._dog_connectors[miner["dog_id"]-1].register_miner(name, ip)
                    miner_found = True

                except Exception as e:
                    logging.error("Can not add new miner " + name + "! Miner was found and watchdog returns an error.")
                    logging.error(e)
                    return False

        if not miner_found:
            self._all_miners.append({"name": name, "ip": ip, "dog_id": None})
        return True

    def find_miner(self, name):
        if not name:
            raise Exception("Name of miner and id of watchdog needs to bind it!")

        for miner in self._all_miners:
            if miner["name"] == name:
                return miner
        return None

    def bind_miner(self, name, dog_id, dog_ip):
        if not name or (not dog_id and not dog_ip):
            raise Exception("Name of miner and id or IP of watchdog needs to bind it!")

        if not dog_id:
            for index, dog in enumerate(self._dog_connectors):
                if dog.address == dog_ip:
                    dog_id = index + 1

        dog_id = int(dog_id)
        miner = self.find_miner(name)
        if not miner:
            logging.error("Can not bind miner " + name + ", because miner is not registered!")
            return False

        try:
            self._dog_connectors[dog_id - 1].register_miner(name, miner["ip"])
            miner["dog_id"] = dog_id
            return True

        except Exception as e:
            logging.error("Can not bind miner " + name + "! Miner was found, but watchdog returns an error.")
            logging.error(e)
            return False

    def unbind_miner(self, name):

        miner = self.find_miner(name)
        if not miner:
            raise Exception("Can not unbind miner, because it's not registered!")

        if miner["dog_id"]:
            try:
                self._dog_connectors[miner["dog_id"]-1].remove_miner(name)
                miner["dog_id"] = None
                return True

            except Exception as e:
                logging.error("Can not unbind miner " + name + "! Miner was found, but watchdog returns an error.")
                logging.error(e)
                return False

        logging.error("Can not unbind miner, because it's not under the dog.")
        return False

    def remove_miner(self, name):

        miner = self.find_miner(name)
        if miner:
            try:
                self.unbind_miner(name)
                self._all_miners.remove(miner)
                return True

            except Exception as e:
                logging.error("Can not remove miner!")
                logging.error(e)
                return False

        logging.error("Can not remove miner! Miner " + name + " not found.")
        return False

    def all_miners(self):
        return self._all_miners
