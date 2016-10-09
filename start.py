from masterDog import MasterDog
import time


master = MasterDog("masterDog.conf")

while True:
#    try:
    master.update_stats()

#    except Exception as e:
#        print(e)

    time.sleep(1)