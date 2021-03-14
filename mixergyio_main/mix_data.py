#! /usr/bin/env python3

import argparse
import csv
import datetime
import getpass
import time

from user_rest import UserREST


headers = ['serialNumber',
           'recordedTime',
           'receivedTime',
           'topTemperature',
           'bottomTemperature',
           'charge',
           'frequency',
           'voltage',
           'current',
           'energy',
           'state'
           ]



def get_ms(t, offset=None):
    if t.isdigit():
        t = int(t)
    else:
        t = datetime.datetime.strptime(t, '%Y-%m-%d')
        if offset is not None:
            t += offset
        t = time.mktime(t.timetuple())

    t = int(t) * 1000

    return t

args = {
    'start': 1614080470,
    'end': 1614266885,
    'username': 'damon@owensquare.coop',
    'password': "SyM818^M5h",
    # 'tank': '206e838f-6cd2-4dcf-b987-20b88faeff98',
    'host': 'www.mixergy.io',
    'output': time.strftime('%Y%m%d-%H%M%S') + '.csv'
}

def main(args, offset=None):
    start = args['start']
    end = args['end']

    # password = getpass.getpass('Password: ')
    password = args['password']


    with UserREST(args['host'], args['username'], password) as ur:
        tanks = ur.get_tanks()

        if 'tank' in args:
            tanks = { args['tank'] : tanks[args['tank']] }

        with open(args['output'], "w") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(headers)

            step = 100000000

            for sn, tank in tanks.items():
                tank = ur.get_tank(tank)

                s = start
                e = end

                while s < e:
                    next = s + step

                    # If the requested data range is beyond the next step, go to the end
                    if next > e:
                        next = e

                    measurements = ur.get_tank_measurements(tank, s, next)
                    for measurement in measurements['content']:
                        data = [ sn ] + [ measurement.get(h, '') for h in headers[1:] ]
                        csv_writer.writerow(data)
                    s += step



if __name__ == "__main__":
    main(args)
