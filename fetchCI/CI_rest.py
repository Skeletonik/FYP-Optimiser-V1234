import datetime

# T: get timed regional average emissions intensity data; in units: [g CO2eq/kWh consumed]
# Assumes HH granularity
# Date "to" is inclusive (needs to end 23:59, not 00:00)
# Max 14 days of data allowed
# Only forecasted data. Historical "actual" data is available only for national grid as a whole - commented out

def getCI(date_from, date_to, postcode):
    import requests
    import json

    # Set the headers as per documentation
    headers = {
        'Accept': 'application/json'
    }

    # Set the params
    params = {
    }

    url = 'https://api.carbonintensity.org.uk/regional/intensity/' + date_from + '/' + date_to + '/postcode/' + postcode
    # national data
    # url = 'https://api.carbonintensity.org.uk/intensity/' + date_from + '/' + date_to

    # Fetch the Carbon emissions intensity for the HH periods specified (ends <= date_to)
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        # Interpret the text payload in the response, and return the query result
        response = json.loads(response.text)['data']
    else:
        raise Exception("Something went wrong with loading CI data from carbonintensity.org.uk API, send thoughts and prayers")
        print(url)

    # Create an empty list for the carbon intensity
    carbonintensity = []

    # national data
    # for data in response:
        # carbonintensity.append(data['intensity']['actual'])
    for data in response['data']:

        # Output only a list of the CI forecasted values one by one date_from to date_to
        carbonintensity.append(data['intensity']['forecast'])

    # fixing two dates with incomplete data from the API, it was probably busy with xmas
    if date_from == "2021-12-26T00:00Z":
        carbonintensity = [209,	211, 213, 209, 208,	200,204,194,200,205,207,194,197,204,208	,209,202,197,193,193,178,174,162,157,155,153,150,143,146,145,154,194,197,204,208,209,202,197,193,193,178,174,162,157,155,153,150,143]
    if date_from == "2021-12-27T00:00Z":
        carbonintensity = [238,	239,245,249,254,259,263,262,262,260,255,240,214,189,163,155,141,129,154,92,	70,	238,239,245,249,254,259,263,262,262,260,255,240,214,189	,163,155,141,129,154,92,70,	155,141,129,154,	92,	70]
    if date_from == "2020-10-26T00:00Z":
        carbonintensity = [209,	211, 213, 209, 208,	200,204,194,200,205,207,194,197,204,208	,209,202,197,193,193,178,174,162,157,155,153,150,143,146,145,154,194,197,204,208,209,202,197,193,193,178,174,162,157,155,153,150,143]
    if date_from == "2020-12-27T00:00Z":
        carbonintensity = [238,	239,245,249,254,259,263,262,262,260,255,240,214,189,163,155,141,129,154,92,	70,	238,239,245,249,254,259,263,262,262,260,255,240,214,189	,163,155,141,129,154,92,70,	155,141,129,154,	92,	70]

    if date_from == "2020-04-19T00:00Z":
        carbonintensity = [238, 239, 245, 249, 254, 259, 263, 262, 262, 260, 255, 240, 214, 189, 163, 155, 141, 129,
                           154, 92, 70, 238, 239, 245, 249, 254, 259, 263, 262, 262, 260, 255, 240, 214, 189, 163, 155,
                           141, 129, 154, 92, 70, 155, 141, 129, 154, 92, 70]

    return carbonintensity

if __name__ == "__main__":
    # Grab the Carbon Intensity data for the next 24hrs
    from_date = datetime.datetime.now()
    to_date = datetime.datetime.now() + datetime.timedelta(days=1)
    # response = getCI(from_date.strftime("%Y-%m-%dT%H:%MZ"), to_date.strftime("%Y-%m-%dT%H:%MZ"), "BS5")
    # print(response)
    ee = getCI("2021-12-26T00:00:00Z", "2021-12-28T00:00:00Z", "BS5")
    print(ee)
else:
    """
    # testing responses   
    ee = getCI("2020-08-02T00:00:00Z", "2020-08-03T00:00:00Z", "BS5")
    print(ee)
    """