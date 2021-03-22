from datetime import datetime

def loadFromJSON (filename:str):
    import json
    with open(filename, 'r') as infile:
        return json.load(infile)

def saveAsJSON (filename:str, data:dict):
    import json
    with open(filename, 'w') as outfile:
        json.dump(data, outfile)

def floatify (row:dict, fields:list) -> dict:
    """ make the fields specified in to floats"""
    for field in fields:
        row[field] = float(row[field])
    return row

def datetimeify (string:str) -> datetime.date:
    """Test for the different datetime string formats I'm expecting to encounter, and parse as appropriate"""
    import re

    # Ditch the slashes - they always replace hyphens in any date(time) format
    string = string.replace('/', '-')

    # Break the imported string to time and date
    # Acceptable time/date delimiters are ' ', T (and + for timezones)
    # Acceptable delimiters within time/date are - and :
    # If there's no tz (i.e. it ends in Z), or if there's no third part, we'll set the last slot to '' (blank string)
    [date, time, tz] = (re.split(' |T|\+|Z', string) + ['', ''])[:3]
    date_split = re.split('-|:', date)

    # Establish the format we've got
    date_format   = "%d-%m-%Y" if len(date_split[0]) == 2 else "%Y-%m-%d"
    time_format   = "%H:%M:%S" if time != '' else ''

    # We'll just bin the TZ for now because it doesn't impact me
    string_format = date_format + "T" + time_format
    string        = date + "T" + time

    return datetime.strptime(string, string_format)

if __name__ == "__main__":
    
    print(datetimeify("2016-01-13 00:03:27"))
    print(datetimeify("01/02/2017"))
    