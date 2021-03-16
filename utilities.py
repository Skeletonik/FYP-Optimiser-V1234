from datetime import datetime

def loadFromJSON (filename:str):
    import json
    with open(filename, 'r') as infile:
        return json.load(infile)

def saveAsJSON (filename:str, data:object):
    import json
    with open(filename, 'w') as outfile:
        json.dump(data, outfile)

def floatify (row:object, fields:list) -> object:
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

# def datetimeify (string:str) -> datetime.date:
#     """Test for the different datetime string formats I'm expecting to encounter, and parse as appropriate"""
#     import re

#     # Ditch the slashes - they always replace hyphens in any date(time) format
#     string = string.replace('/', '-')

#     # Break the imported string to time and date
#     # Acceptable time/date delimiters are ' ', T (and + for timezones)
#     # Acceptable delimiters within time/date are - and :
#     [date, time, tz] = (re.split(' |T|\+', string) + [False])[:3]
#     # disassembled = [re.split('-|:', part) for part in date]
#     date_split = re.split('-|:', date)

#     # Establish the format we've got
#     date_format = "%d-%m-%Y" if len(date_split[0] = 2) else "%Y-%m-%d"
#     time_format = ""

    
#     # Also look at the characters which were used to delimit
#     #no_digits = re.sub('\d', '', string)

#     # We're just going to assume this input is date, day and bin the TZ because we're UTC anyway (sometimes)
#     parsing_date = disassembled[0]
#     # Check if it's DD-MM-YYYY
#     if len(parsing_date[0]) == 2:
#         parsing_date[0] = disassembled[0][2]
#         parsing_date[1] = disassembled[0][1]
#         parsing_date[2] = disassembled[0][0]
#     else:
#         parsing_date
    


#     date   = True if no_digits[0] is '-'
#     time   = True 




#     # Check we're YYYY-MM-DD. If we're DD-MM-YYYY, swap it round


#     # DATETIME-COMPATIBLE ISO FORMAT
#     # Remove the actual digits, so we just have the formatting
#     no_digits = re.sub('\d', '', string)
#     # These are the acceptable formats. The regex was scary, this is nicer
#     if no_digits in ['--', '-- ::', '--T::', '-- ::.', '-- ::.+:', '--T::+']:
#         return datetime.fromisoformat(string)

#     # regex test for dates only
#     # if re.compile()

#     # regex for accepted by datetime.fromisoformat


#     # Datetime supports the following formats with .fromisoformat
#     # ISO Format with a Z
#     if "Z" in string:
#         # Python does not recognize Z format - guy on StackOverflow
#         string.replace('Z', '+00:00')
#         return datetime.fromisoformat(string)
#     # ISO Format without a Z
#     if "T" in string:
#         return datetime.fromisoformat(string)


if __name__ == "__main__":
    
    print(datetimeify("2016-01-13 00:03:27"))
    print(datetimeify("01/02/2017"))
    