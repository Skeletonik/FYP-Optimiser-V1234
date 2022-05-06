""" Very definitely a top-level function
Takes a list of dates and times. Applies them to *every variable*. 
Sources *every variable* from its CSV, or the Mixergy API
Calculates APX and SSP costs for later analysis in Excel
T: emissions as well, but only HWT optimisation
"""

import csv
from copy import deepcopy
import datetime

from utilities import loadFromJSON
from utilities import recursiveReplace
from utilities import listProduct
from utilities import sumProduct
from utilities import listSum

import runOptimizerV12
stock_config = loadFromJSON('./input_data/systemconfig-v5.json')

csv_headers = ["duration (h)", "elecgen_date_from", "tank_date_from", "real kWh", "sim kWh", "Real APX Cost", "Real SSP Cost", "Sim APX Cost", "Sim SSP Cost", "sim_import", "sim_selfcon", "real CO2", "Sim CO2", "lp_duration"]

# Function which returns, as a string, a date deltadays from initial_date
def strfdelta (initial_date, delta_days):
    return (initial_date+datetime.timedelta(days=delta_days)).strftime("%Y-%m-%dT%H:%M:%S")

# Starting dates for tank and elec/gen
tank_date = datetime.datetime(2021, 11, 20)
elecgen_date = datetime.datetime(2021, 11, 20)
tank_date2 = datetime.datetime(2021, 11, 20)

# Make arrays with those deltas
# For 24hr period
tank_dates = [[strfdelta(tank_date, delta)] for delta in range(0, 1)]
elecgen_dates = [[strfdelta(elecgen_date, delta)] for delta in range(0, 42)]
tank_dates2 = [[strfdelta(tank_date2, delta)] for delta in range(0, 1)]

# Duration in hours of optimisation
duration = 24

print("running ", len(elecgen_dates), "scenarios:")

with open('./longRun/longrun-' + str(duration) + '-ECC-N.csv', 'w', newline='') as csvfile:
    
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow(csv_headers)

    i = 0

    for run_date in elecgen_dates:
        # Avoid the system config getting changed, because that happens as (e.g.) strings are turned to objects
        system_config = deepcopy(stock_config)

        new_tank_date = tank_date + datetime.timedelta(days=i)
        new_tank_dates = [[strfdelta(new_tank_date, delta)] for delta in range(0, 1)]
        new_tank_date2 = tank_date2 + datetime.timedelta(days=i)
        new_tank_dates2 = [[strfdelta(new_tank_date2, delta)] for delta in range(0, 1)]
        i = i + 1
        # Swap the dates out as we want them
        system_config['optimization_duration'] = duration

        date_from = run_date[0]
        tank_date_from = new_tank_dates[0][0]
        tank_date_from2 = new_tank_dates2[0][0]

        # Change all the from dates to align on the specified one
        system_config = recursiveReplace(system_config, "date_from", date_from)
        # Tank from dates are different
        # system_config['tanks'] = recursiveReplace(system_config['tanks'], "date_from", tank_date_from)
        system_config['tanks']['data']['ECC']['date_from'] = tank_date_from
        system_config['tanks']['data']['Nursery']['date_from'] = tank_date_from2
        # system_config['tanks']['data']['Damon']['date_from'] = tank_date_from2
        new_conf = system_config

        # Call the optimizer
        optimized = runOptimizerV12.main(new_conf)
        lp_duration = optimized['lp_duration']
        system = optimized['system']
        solution = optimized['solution']

        ## PROCESS SIM DATA
        # Grab all the i(t)'s, and sum them at any time period to get system_i
        # This gives you system import power at t
        # Likewise for self_consumption
        # Remember, these are in kW, not kWh, so need converting
        sim_i = [
            sum(i)* (system_config['supply_period_duration']/60) 
                for i in zip(*[solution[tank]['i'] for tank in system['tanks']])
        ]
        sim_s = [
            sum(s)* (system_config['supply_period_duration']/60) 
                for s in zip(*[solution[tank]['s'] for tank in system['tanks']])
        ]
        # TBD - fix supply_period_duration
        sim_kWh      = (sum(sim_i) + sum(sim_s))                                                 
        sim_APX_cost = (sumProduct(sim_i, system['I']) + sumProduct(sim_s, system['X']))
        sim_SSP_cost = (sumProduct(sim_i, system['paidI']) + sumProduct(sim_s, system['paidX']))
        sim_import   = sum(sim_i)
        sim_selfcon  = sum(sim_s)

        ## PROCESS REAL DATA
        timeslots = range(len(system['I']))
        # real_E is the sum of all tank E's
        # E is in ***kWh***. Remember, i and s now in kWh
        real_E = [
            sum(E_t) 
                for E_t in zip(*[system['tanks'][tank].realworldE() for tank in system['tanks']])
        ]

        # T: real_E, G  in kWh
        G_kWh = [system['G'][t] for t in timeslots]

        # Disassemble to s and i, exactly like the optimiser does
        # real_s is the lower of demand or generation (so selfcon first)
        real_s = [min(real_E[t], G_kWh[t]) for t in timeslots]

        # real_i is what's left over after self-consumption
        real_i = [real_E[t] - real_s[t] for t in timeslots]

        # Then we just follow the same process as for the sim data
        real_kWh      = (sum(real_i) + sum(real_s))                                                 
        real_APX_cost = (sumProduct(real_i, system['I']) + sumProduct(real_s, system['X']))
        real_SSP_cost = (sumProduct(real_i, system['paidI']) + sumProduct(real_s, system['paidX']))
        real_import   = sum(real_i)
        real_selfcon  = sum(real_s)
        real_carbon = (sumProduct(real_i, system['E']) + sumProduct(real_s, system['E']))
        sim_carbon = (sumProduct(sim_i, system['E']) + sumProduct(sim_s, system['E']))
        
        # Append the row
        writer.writerow([duration, date_from, tank_date_from, real_kWh, sim_kWh, real_APX_cost, real_SSP_cost, sim_APX_cost, sim_SSP_cost, sim_import, sim_selfcon, real_carbon, sim_carbon, lp_duration])

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