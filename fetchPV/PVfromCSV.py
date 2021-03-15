import csv
import datetime

# sledgehammer, walnut, we meet again
import os, sys
sys.path.append(os.path.relpath('./'))
# pylint: disable=import-error
from utilities import floatify

def importCSV (filename:str, date_from:datetime.date, date_to:datetime.date) -> list:
    """ Load energy pricing data from Damon's CSVs to a python object in a format we like
    Note this function assumes 30min periods
    """
    # Ensure both dates are datetime objects
    for x in [date_from, date_to]:
        if type(x) is not datetime.datetime:
            raise Exception("Expected a datetime object, got a ", type(x))

    imported_data = []
    with open(filename, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            # Grab and parse the date and time
            # Supply Period gives time within day, add it as a timedelta from midnight
            row['START'] = datetime.datetime.strptime(row['START'], "%Y-%m-%d  %H:%M:%S")
            # See if the date and time are within the from/to range
            if date_from <= row['START'] < date_to:
                imported_data.append(floatify(row, ['EXPORT', 'IMPORT']))

    return imported_data

def makeGList (imported_data):
    G = []
    for row in imported_data:
        # Looking at the data, I want Import to be the generation really
        # This is data for one meter, ~1/4 of total capacity
        G.append(row['IMPORT']*4)
    return G

def main(filename, date_from, date_to):
    imported_data = importCSV(filename, date_from, date_to)
    G = makeGList(imported_data)
    return G


if __name__ == '__main__':
    # 1am (SP3) on 2020/09/01
    date_from = datetime.datetime(2020, 9, 1, 1)
    # 1pm (SP27?) on 2020/09/01
    date_to = datetime.datetime(2020, 9, 1, 13)
    returned = main('./input_data/damons_ECC-gen-meter-intervals.csv', date_from, date_to)
    print(returned)