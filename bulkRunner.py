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
stock_config = loadFromJSON('./input_data/systemconfig-v3.json')

csv_rows = [["tank_date_from", "tank_date_to", "elecgen_date_from", "elecgen_date_to", "real kWh", "sim kWh", "Real APX Cost", "Real SSP Cost", "Sim APX Cost", "Sim SSP Cost", "sim_import", "sim_selfcon"]]

def strfday (day):
    return datetime.datetime(2021, 3, day).strftime("%Y-%m-%dT%H:%M:%S")
# list_of_dates = [["2021-01-28T00:00:00","2021-01-29T00:00:00"]]
# We have a limited amount of tank data, so stay in that window
tank_dates = [[strfday(day), strfday(day+1)] for day in range(1, 15)]

def strfdelta (days):
    start_date = datetime.datetime(2021, 1, 1)
    return (start_date+datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")
# We have a lot more meter data. >100 days from Jan 1st, so we'll just do all that.
elecgen_dates = [[strfdelta(day), strfdelta(day+1)] for day in range(1, 53)]

list_of_dates = []
for tank_date in tank_dates:
    for elecgen_date in elecgen_dates:
        list_of_dates.append(tank_date+elecgen_date)

print("running ", len(list_of_dates), "scenarios:")

for date_pair in list_of_dates:
    # Avoid the system config getting changed, because that happens as (e.g.) strings are turned to objects
    system_config = deepcopy(stock_config)
    
    # Swap the dates out as we want them
    tank_date_from = date_pair[0]
    tank_date_to   = date_pair[1]
    elecgen_date_from = date_pair[2]
    elecgen_date_to   = date_pair[3]
    # Temporarily commented out whilst I wait for March data from Damon
    # new_conf = recursiveReplace(system_config, "date_from", date_from)
    # new_conf = recursiveReplace(system_config, "date_to", date_to)
    system_config = recursiveReplace(system_config, "date_from", elecgen_date_from)
    system_config = recursiveReplace(system_config, "date_to", elecgen_date_to)
    system_config['tanks'] = recursiveReplace(system_config['tanks'], "date_from", tank_date_from)
    system_config['tanks'] = recursiveReplace(system_config['tanks'], "date_to", tank_date_to)
    new_conf = system_config

    # Call the optimizer
    optimized = runOptimizer.main(new_conf)
    system = optimized['system']
    solution = optimized['solution']

    # Real energy consumption is sum(E). E = kWh used in 30min periods
    # sum(E) gives day's consuption for tank
    # sum(sum([for tank in tanks])) gives total days consumption for all tanks
    real_kWh = sum([sum(system['tanks'][tank].realworldE()) for tank in system['tanks']])
    
    # Sim energy consumption is sum(kW * (supply period as fractional hr)) = kWh
    sim_kWh = sum([ 
        sumProduct(
            (solution[tank]['i']+solution[tank]['s']), (system['tanks'][tank].supply_period_duration/60)
        ) for tank in system['tanks']
    ])
    # [(kWh/h * p/kWh) * (fractional hr) = p] for each tank
    real_APX_cost = sum([sumProduct(system['tanks'][tank].realworldE(), system['I']) for tank in system['tanks']])
    # [(kWh/h * p/kWh) * (fractional hr) = p] for each tank
    real_SSP_cost = sum([ 
        sumProduct(
            system['tanks'][tank].realworldE(), system['paidI']
        ) for tank in system['tanks']
    ])
    sim_APX_cost = sum([ 
        sumProduct(
            listSum(listProduct(solution[tank]['i'], system['I']), listProduct(solution[tank]['s'], system['X'])), (system['tanks'][tank].supply_period_duration/60)
        ) for tank in system['tanks']
    ])
    # [(kWh/h * p/kWh) * (fractional hr) = p] for each tank
    sim_SSP_cost = sum([ 
        sumProduct(
            listSum(listProduct(solution[tank]['i'], system['paidI']), listProduct(solution[tank]['s'], system['paidX'])), (system['tanks'][tank].supply_period_duration/60)
        ) for tank in system['tanks']
    ])
    # [sum of kw/30min import power for all times and tanks]/2 = kWh
    sim_import = sum([
        sum(solution[tank]['i'])
            for tank in system['tanks']
    ])/2
    # [sum of kw/30min self-consumed power for all times and tanks]/2 = kWh
    sim_selfcon = sum([
        sum(solution[tank]['s'])
            for tank in system['tanks']
    ])/2
    # Append the row
    # Copy everything to stop the stupid soft copies breaking things
    # csv_rows.append([deepcopy(var) for var in [date_from, date_to, real_kWh, sim_kWh, real_APX_cost, real_SSP_cost, sim_APX_cost, sim_SSP_cost]])
    csv_rows.append([tank_date_from, tank_date_to, elecgen_date_from, elecgen_date_to, real_kWh, sim_kWh, real_APX_cost, real_SSP_cost, sim_APX_cost, sim_SSP_cost, sim_import, sim_selfcon])

# Write out to CSV
with open('./bulkrun-huge.csv', 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for row in csv_rows:
            writer.writerow(row)