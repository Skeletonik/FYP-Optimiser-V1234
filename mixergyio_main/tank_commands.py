#! /usr/bin/env python3

# Thom Chase
# Cepro
# 02-12-20

# Quick Script to show commands avalible for a Mixergy Tank. Based on the code provided by Mixergy. This script relies on the Mixergy user_rest.py and other scripts to work.

import requests
import json
import datetime
import time
from user_rest import UserREST


username = "damon@owensquare.coop"
password = "psw"
host = "www.mixergy.io"

def main():

    with UserREST(host, username, password) as ur:
        tanks = ur.get_tanks()
        #print("--------------------------TANKS-----------------------")
        #print(tanks)
        
        for sn, tank in tanks.items():
            tank = ur.get_tank(tank)
            print("--------------------------TANK-----------------------")
            print(tank)
        
            print("--------------------------TANK MEASUREMENTS-----------------------")
            
            #today = datetime.date.today()
            #yesterday = today - datetime.timedelta(days = 1)
            #tomorrow = today + datetime.timedelta(days = 1) 
            
            #start = time.mktime(today.timetuple())
            #end = time.mktime(tomorrow.timetuple())
            
            #measurements = ur.get_tank_measurements(tank, start=None, end=None)
            
            #for measurement in measurements["content"]:
                #print(measurement)
            
            print("--------------------------LATEST MEASUREMENT-----------------------")
            
            latest = ur.get_tank_latest_measurement(tank)
            
            print(latest)
            
            print("--------------------------SCHEDULE-----------------------")
            
            schedule = ur.get_tank_schedule(tank)
            
            print(schedule)
            
            print("--------------------------PUT COMMAND-----------------------")
            
            control = {"charge": 65}

            command = ur.put_tank_control(tank, control)
        
if __name__ == "__main__":
    main()