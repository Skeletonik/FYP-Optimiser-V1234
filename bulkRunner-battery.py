""" Very definitely a top-level function
Takes a list of dates and times. Applies them to *every variable*. 
Sources *every variable* from its CSV, or the Mixergy API
Calculates APX and SSP costs for later analysis in Excel """

import csv
from copy import deepcopy
import datetime

from utilities import loadFromJSON
from utilities import recursiveReplace
from utilities import listProduct
from utilities import sumProduct
from utilities import listSum

import runOptimizer
stock_config = loadFromJSON('./input_data/systemconfig-v5.json')

csv_headers = ["duration (h)", "tank_date_from", "elecgen_date_from", "Real APX Cost", "Sim APX Cost", "Real SSP Cost", "Sim SSP Cost", "batt_in", "batt_out", "real_import", "sim_import", "real_export", "sim_export", "real_carbon", "sim_carbon", "lp_duration"]

# Function which returns, as a string, a date deltadays from initial_date
def strfdelta (initial_date, delta_days):
    return (initial_date+datetime.timedelta(days=delta_days)).strftime("%Y-%m-%dT%H:%M:%S")

# Starting dates for Mixergy tank and elec/gen
tank_date = datetime.datetime(2022, 1, 5)
elecgen_date = datetime.datetime(2022, 1, 5)
tank_date2 = datetime.datetime(2022, 1, 5)

# Make arrays with those deltas
# For 24hr period, 1-14 and 0-52
tank_dates = [[strfdelta(tank_date, delta)] for delta in range(0, 2)] # Until 14 Mar
elecgen_dates = [[strfdelta(elecgen_date, delta)] for delta in range(0, 2)]
tank_dates2 = [[strfdelta(tank_date2, delta)] for delta in range(0, 2)]

# Duration in hours of optimisation
duration = 24

list_of_dates = []
tank_dates = zip(tank_dates, tank_dates2)
for tank_date in tank_dates:
    for elecgen_date in elecgen_dates:
        list_of_dates.append([duration]+tank_date[0]+elecgen_date+tank_date[1])

print("running ", len(list_of_dates), "scenarios:")

with open('./bulkRun/bulkrun-' + str(duration) + '-ECC-Nursery-newOF-fulldata.csv', 'w', newline='') as csvfile:
    
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow(csv_headers)

    for date_pair in list_of_dates:
        # Avoid the system config getting changed, because that happens as (e.g.) strings are turned to objects
        system_config = deepcopy(stock_config)
        
        # Swap the dates out as we want them
        optimization_duration = date_pair[0]
        tank_date_from        = date_pair[1]
        elecgen_date_from     = date_pair[2]
        tank_date_from2        = date_pair[3]

        system_config['optimization_duration'] = optimization_duration
        # Change all the from dates to align on the specified one
        system_config = recursiveReplace(system_config, "date_from", elecgen_date_from)
        # Tank from dates are different
        # system_config['tanks'] = recursiveReplace(system_config['tanks'], "date_from", tank_date_from)
        system_config['tanks']['data']['ECC']['date_from'] = tank_date_from
        system_config['tanks']['data']['Nursery']['date_from'] = tank_date_from2
        # system_config['tanks']['data']['Damon']['date_from'] = tank_date_from2

        # set new configuration file
        new_conf = system_config

        # Call the optimizer
        optimized = runOptimizer.main(new_conf)
        lp_duration = optimized['lp_duration']
        system = optimized['system']
        solution = optimized['solution']

        ## PROCESS SIM DATA
        # Grab all the i(t)'s, and sum them at any time period to get system_i
        # This gives you system import power at t
        # Likewise for self_consumption
        # Remember, these should be in kWh
        # sim_p = [
          #   sum(i)
            #     for i in zip(*[solution['pECC'] solution['pNursery'] for tank in system['tanks']])
        # ]
        #sim_s = [
         #   sum(s)
          #      for s in zip(*[solution[tank]['s'] for tank in system['tanks']])
        # ]
        # TBD - fix supply_period_duration - not
        # sim

        # sim_kWh      = (sum(solution['pECC']) + sum(solution['pNursery']))

        sim_APX_cost = (sumProduct(solution['m'], system['I']) + sumProduct(solution['e'], system['X']))
        sim_SSP_cost = (sumProduct(solution['m'], system['paidI']) + sumProduct(solution['e'], system['paidX']))
        sim_carbon = (sumProduct(solution['m'], system['E']) + sumProduct(solution['e'], system['E']))

        sim_imp = sum(solution['m'])
        sim_exp = sum(solution['e'])
        batt_imp   = sum(solution['z'])
        batt_exp  = sum(solution['y'])

        ## PROCESS REAL DATA
        timeslots = range(len(system['I']))
        # real_E is the sum of all tank E's
        # E is in ***kWh***. Remember, i and s now in kWh
        real_E = [
            sum(E_t) 
                for E_t in zip(*[system['tanks'][tank].realworldE() for tank in system['tanks']])
        ]

        # T: real_E still in kWh; G in kW
        # T: all in kW here?? at least it is for all the tanks together
        # T: changing G to be in kWh from kW
        G_kWh = [system['G'][t]/2 for t in timeslots]

        # Disassemble to s and i, exactly like the optimiser does
        # real_s is the lower of demand or generation (so selfcon first)
        # real_s = [min(real_E[t], G_kWh[t]) for t in timeslots]

        # real_i is what's left over after self-consumption
        # real_i = [real_E[t] - real_s[t] for t in timeslots]

        # Then we just follow the same process as for the sim data
        # real_kWh      = (sum(real_i) + sum(real_s))
        real_APX_cost = (sumProduct(system['SM']['IMP'], system['I']) + sumProduct(system['SM']['EXP'], system['X']))
        real_SSP_cost = (sumProduct(system['SM']['IMP'], system['paidI']) + sumProduct(system['SM']['EXP'], system['paidX']))
        real_carbon = (sumProduct(system['SM']['IMP'], system['E']) + sumProduct(system['SM']['EXP'], system['E']))

        real_imp = sum(system['SM']['IMP'])
        real_exp = sum(system['SM']['EXP'])
        # real_import   = sum(real_i)
        # real_selfcon  = sum(real_s)
        
        # Append the row
        # "duration (h)", "tank_date_from", "elecgen_date_from", "Real APX Cost", "Sim APX Cost","Real SSP Cost",  "Sim SSP Cost",  "batt_in", "batt_out", "real_import", "sim_import", "real_export", "sim_export", "real_carbon", "sim_carbon", "lp_duration"]
        writer.writerow([optimization_duration, tank_date_from, elecgen_date_from, real_APX_cost, sim_APX_cost, real_SSP_cost, sim_SSP_cost, batt_imp, batt_exp, real_imp, sim_imp, real_exp, sim_exp, real_carbon, sim_carbon, lp_duration])

        """ original real E & S by Seb
        # E is in ***kWh***. Remember, i and s now in kWh
        real_E = [
            sum(E_t)
            for E_t in zip(*[system['tanks'][tank].realworldE() for tank in system['tanks']])
        ]
        # Disassemble to s and i, exactly like the optimiser does
        # real_s is the lower of demand or generation (so selfcon first)
        real_s = [min(real_E[t], system['G'][t]) for t in timeslots]
        # real_i is what's left over after self-consumption
        real_i = [real_E[t] - real_s[t] for t in timeslots]
        """