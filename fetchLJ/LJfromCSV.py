import csv
import datetime

def timedeltaFromSP(supply_period):
    """ Calculate the time within the day given by a supply period. Return as a 
    timedelta to find the time within the day the price is valid for """
    # zero-index the supply period (for midnight start)
    supply_period = int(supply_period)-1
    return datetime.timedelta(hours=0.5*supply_period)

def importCSV (filename:str, date_from:datetime.date, date_to:datetime.date) -> list:
    """ Load energy pricing data from Damon's CSVs to a python object in a format we like
    Note this function assumes 30min periods """
    # Ensure both dates are datetime objects
    for x in [date_from, date_to]:
        if type(x) is not datetime.datetime:
            raise Exception("Expected a datetime object, got a ", type(x))

    pricing_data = []
    with open(filename, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            # Grab and parse the date and time
            # Supply Period gives time within day, add it as a timedelta from midnight
            date_now = datetime.datetime.strptime(row['Date'], "%d/%m/%Y") + timedeltaFromSP(row['SP'])
            # See if the date and time are within the from/to range
            if date_from <= date_now < date_to:
                pricing_data.append(row)

    return pricing_data

def makeIAndXTariffs (pricing_data:list) -> list:
    I_components = ['APX HH', 'SSP', 'BSUoS Price', 'GDoUS Price', 'DUoS Price']
    X_components = ['APX HH']
    tariffs = {
        "I":[],
        "X":[]
    }
    for row in pricing_data:
        # Sum the components which make each price, to make a list of price WRT time
        I = sum([float(row[cost])/10 for cost in I_components])
        X = sum([float(row[cost])/10 for cost in X_components])
        tariffs['I'].append(I)
        tariffs['X'].append(X)
    return tariffs

def main (filename, date_from, date_to) -> object:
    pricing_data = importCSV('./input_data/damons_HH_combined.csv', date_from, date_to)
    tariffs = makeIAndXTariffs(pricing_data)
    return tariffs

if __name__ == '__main__':
    # 1am (SP3) on 2020/09/01
    date_from = datetime.datetime(2020, 9, 1, 1)
    # 1pm (SP27?) on 2020/09/01
    date_to = datetime.datetime(2020, 9, 1, 13)
    returned = main('./input_data/damons_HH_combined.csv', date_from, date_to)
    print(returned)

