import csv
import datetime

# sledgehammer, walnut, we meet again
import os, sys
sys.path.append(os.path.relpath('./'))
# pylint: disable=import-error
from utilities import datetimeify

# T: Smart Meter readings loader -> total OSCE imports and exports

def importCSV (filename:str, date_from:datetime.date, date_to:datetime.date) -> list:
    """ Load OSCE Smart Meter electricity Import & Export data from Damon's CSVs to a python dict in a format we like
    Note this function assumes 30min periods """
    # Ensure both dates are datetime objects
    for x in [date_from, date_to]:
        if type(x) is not datetime.datetime:
            raise Exception("Expected a datetime object, got a ", type(x))

    # get separately the total OSCE import and export with the distribution grid
    metering_data = {
        'EXP': [],
        'IMP': []
    }
    with open(filename, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            # Grab and parse the date
            date_now = datetimeify(row['created_at'])
            # See if the date and time are within the from/to range

            if date_from <= date_now < date_to:
                exports = row['exports']
                imports = row['imports']
                metering_data['EXP'].append(float(exports))
                metering_data['IMP'].append(float(imports))

    return metering_data


# T: maybe needed - changing file path to .. - for testing ; " . " for running
def main (filename, date_from, date_to) -> dict:

    metering_data = importCSV(filename, date_from, date_to)

    return metering_data

if __name__ == '__main__':
    # 1am (SP3) on 2020/09/01
    date_from = datetime.datetime(2022, 1, 1, 0)
    # 1pm (SP27?) on 2020/09/01
    date_to = datetime.datetime(2022, 1, 2, 0)

    returned = main('./../input_data/owensquare-2020-2022-intervals-30min.csv', date_from, date_to)
    print(returned)

