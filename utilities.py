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

def recursiveReplace (obj, replace_key, replace_value):
    """ Replace the value of a dictionary key with replace_value, recursively """
    if replace_key in obj:
        obj[replace_key] = replace_value
    for key in obj:
        if type(obj[key]) == dict:
            obj[key] = recursiveReplace(obj[key], replace_key, replace_value)
    return obj

def listProduct (a:list, b:list) -> list:
    if len(a) == len(b):
        zipped = zip(a, b)    
    return [a*b for a, b in zipped]

def sumProduct (a:list, b:[list, float, int]) -> float:
    if type(b) != list:
        zipped = zip(a, [b*1 for item in a])
    elif len(a) == len(b):
        zipped = zip(a, b)        
    return sum([a*b for a, b in zipped])

def listSum (a:list, b:list) -> list:
    if len(a) == len(b):
        zipped = zip(a, b)    
    return [a+b for a, b in zipped]


if __name__ == "__main__":
    
    print(datetimeify("2016-01-13 00:03:27"))
    print(datetimeify("01/02/2017"))
    