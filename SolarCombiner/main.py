# Read daily PV generation readings with HH granularity and combine them to a continuous CSV for use in optimiser
# readings from combined ~18  kWp out of the total 43 kWp installed
# can be assumed to be a good scaled representation of the total generation
# not the most robust script ever, but it did the job and now it's not needed anymore

import datetime
import csv


def combiner(date_from:datetime.date, date_to:datetime.date, pv_num):

    # assign the appropriate meter IDs to PV array IDs
    if pv_num == 1:
        meter = 'EML1325015594'
    elif pv_num == 2:
        meter = 'EML1325015592'
    elif pv_num == 3:
        meter = 'EML1325015602'
    PV = str(pv_num)

    # probably obsolete
    imported_data = []

    # create a new CSV file for all the data
    # create CSV headers in it
    csv_headers = ["SP", "ReadingPV"]
    dates_range = [start + datetime.timedelta(days=x) for x in range(0, (end - start).days+1)]

    with open('./solar-readings-ECC-PV' + str(pv_num) + '.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(csv_headers)

        # run through the dates we want
        for date in dates_range:
            # print(date.strftime("%d-%m-%Y"))

            # for given date, open the daily CSV file
            # using the naming convention
            file_date = date.strftime("%Y%m%d")

            # data\ECC-Backup-PV-generation\ECC.PV3\EML1325015602-20220328.csv
            filename = './data/ECC-Backup-PV-generation/ECC.PV' + PV + '/' + meter + '-' + file_date + '.csv'

            # print(filename)

            # read the daily CSV file
            with open(filename, mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file)

                # read each row
                for row in csv_reader:

                    # write to the main CSV file the SP and the meter reading in the original formats
                    timestamp = row['created_at']
                    reading = row[meter]
                    writer.writerow([timestamp, reading])
        return imported_data


if __name__ == '__main__':

    # run the main function above
    # select dates to get PV data from, check for full data availability
    # select the ID of the PV array, it only changes the folder name & meter code
    start = datetime.datetime.strptime("15-10-2020", "%d-%m-%Y")
    end = datetime.datetime.strptime("09-04-2022", "%d-%m-%Y")
    pv_array = 3

    # run the combiner that creates the new CSV
    combiner(start, end, pv_array)

