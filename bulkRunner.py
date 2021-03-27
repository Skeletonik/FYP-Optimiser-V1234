""" Very definitely a top-level function
Takes a list of dates and times. Applies them to *every variable*. 
Sources *every variable* from its CSV, or the Mixergy API
Calculates APX and SSP costs for later analysis in Excel """

import csv

from utilities import loadFromJSON
from utilities import recursiveReplace
from utilities import listProduct
from utilities import sumProduct
from utilities import listSum

import runOptimizer
system_config = loadFromJSON('./input_data/systemconfig-v3.json')

csv_rows = [["date_from", "date_to", "real kWh", "sim kWh", "Real APX Cost", "Real SSP Cost", "Sim APX Cost", "Sim SSP Cost"]]

list_of_dates = [["2021-01-28T00:00:00","2021-01-29T00:00:00"]]

for date_pair in list_of_dates:
    # Swap the dates out as we want them
    date_from = date_pair[0]
    date_to   = date_pair[1]
    new_conf = recursiveReplace(system_config, "date_from", date_from)
    new_conf = recursiveReplace(system_config, "date_to", date_to)

    # Call the optimizer
    optimized = runOptimizer.main(new_conf)
    system = optimized['system']
    solution = optimized['solution']

    # Real energy consumption is sum(E). E = kWh used in 30min periods
    real_kWh = sum([sum(system['tanks'][tank].realworldE()) for tank in system['tanks']])
    # Sim energy consumption is sum(kW * (supply period as fractional hr)) = kWh
    sim_kWh = sum([ 
        sumProduct(
            (solution[tank]['i']+solution[tank]['s']), (system['tanks'][tank].supply_period_duration/60)
        ) for tank in system['tanks']
    ])
    # [(kWh/h * p/kWh) * (fractional hr) = p] for each tank
    real_APX_cost = sum([ 
        sumProduct( 
            system['tanks'][tank].realworldE(), system['I']
        ) for tank in system['tanks']
    ])
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
    csv_rows.append([date_from, date_to, real_kWh, sim_kWh, real_APX_cost, real_SSP_cost, sim_APX_cost, sim_SSP_cost])

# Write out to CSV
with open('./bulkrun.csv', 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for row in csv_rows:
            writer.writerow(row)