# sledgehammer, walnut, we meet again
import os, sys
sys.path.append(os.path.relpath('./mixergyio_main'))
# pylint: disable=import-error

from user_rest import UserREST
from processMixergy import processMixergy

def fetchMixergy(time_from, time_to, tank_id):
    username = "damon@owensquare.coop"
    password = "SyM818^M5h"
    host = "www.mixergy.io"

    with UserREST(host, username, password) as ur:
        # tanks = ur.get_tanks()
        # for sn, tank in tanks.items():
            tank = ur.get_tank(tank_id)
            measurements = ur.get_tank_measurements(tank, time_from, time_to)
            print(measurements)

    return {
        'time_from': time_from,
        'time_to'  : time_to,
        'soc_demanded': processMixergy(measurements['content'])
    }

if __name__ == "__main__":
    returned = fetchMixergy(1614470400035, 1614556740084, "MX001224")
    print(returned)