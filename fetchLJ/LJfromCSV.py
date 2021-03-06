import csv
import datetime

# sledgehammer, walnut, we meet again
import os, sys
sys.path.append(os.path.relpath('./'))
# pylint: disable=import-error
from utilities import datetimeify

def timedeltaFromSP(supply_period):
    """ Calculate the time within the day given by a supply period. Return as a 
    timedelta to find the time within the day the price is valid for """
    # zero-index the supply period (for midnight start)
    supply_period = int(supply_period)-1
    return datetime.timedelta(hours=0.5*supply_period)

def importCSV (filename:str, date_from:datetime.date, date_to:datetime.date) -> list:
    """ Load energy pricing data from Damon's CSVs to a python dict in a format we like
    Note this function assumes 30min periods """
    # Ensure both dates are datetime objects
    for x in [date_from, date_to]:
        # print(x)
        if type(x) is not datetime.datetime:
            raise Exception("Expected a datetime object, got a ", type(x))

    pricing_data = []
    with open(filename, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            # Grab and parse the date and time
            # Supply Period gives time within day, add it as a timedelta from midnight
            date_now = datetimeify(row['Date']) + timedeltaFromSP(row['SP'])
            # See if the date and time are within the from/to range
            if date_from <= date_now < date_to:
                pricing_data.append(row)

    return pricing_data

def makeIAndXTariffs (pricing_data:list) -> list:
    I_components = ['APX HH', 'BSUoS Price', 'AAHEDC Price', 'DUoS Price', 'RO', 'FIT', 'CM', 'CFD']
    X_components = ['APX HH', 'BSUoS Price', 'AAHEDC Price', 'GDoUS Price']
    paidI_components = ['SSP', 'BSUoS Price', 'AAHEDC Price', 'DUoS Price', 'RO', 'FIT', 'CM', 'CFD']
    paidX_components = ['SSP', 'BSUoS Price', 'AAHEDC Price', 'GDoUS Price']
    # SSP is wholesale price
    tariffs = {
        "I":[],
        "X":[],
        "paidI":[],
        "paidX":[]
    }
    for row in pricing_data:
        # Sum the components which make each price, to make a list of price WRT time
        # + 4.5136 is a flat "final consumption levy"
        # dividing by 10 to get [p/kWh] from [GBP/MWh]
        I = sum([float(row[cost])/10 for cost in I_components]) + 4.5136
        X = sum([float(row[cost])/10 for cost in X_components])
        paidI = sum([float(row[cost])/10 for cost in paidI_components]) + 4.5136

        paidX = sum([float(row[cost])/10 for cost in paidX_components])
        tariffs['I'].append(I)
        tariffs['X'].append(X)

        tariffs['paidI'].append(paidI)
        tariffs['paidX'].append(paidX)

    return tariffs

# T: changing file path to .. - for testing ; " . " for running
# T: changing to the input file with more data - up to March 2022

def main (filename, date_from, date_to) -> dict:
    # pricing_data = importCSV('./../input_data/damons_HH_combined.csv', date_from, date_to)

    # pricing_data = importCSV('./input_data/damons_HH_combined_20-22_DUoS-21up_NoBattery.csv', date_from, date_to)
    pricing_data = importCSV(filename, date_from, date_to)

    tariffs = makeIAndXTariffs(pricing_data)
    return tariffs

if __name__ == '__main__':
    # 1am (SP3) on 2020/09/01
    date_from = datetime.datetime(2022, 1, 1, 0)
    # 1pm (SP27?) on 2020/09/01
    date_to = datetime.datetime(2022, 1, 3, 13)
    # returned = main('./../input_data/damons_HH_combined.csv', date_from, date_to)

    returned = main('./../input_data/damons_HH_combined_20-22_DUoS-21up_NoBattery.csv', date_from, date_to)
    print(returned)

