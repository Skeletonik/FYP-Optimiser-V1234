import datetime


def APXasList(date_from, date_to):
    # Get APX pricing for the next 24hrs
    APX = getAPX(date_from, date_to)

    pricing = []
    for timeslot in APX:
        pricing.append(timeslot[1]/10)
    return pricing

def getAPX(date_from, date_to, granularity='hh'):
    import requests
    import json

    # Set the headers (Auth token), last update 27/3
    headers = {
        "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MTI5NCwiZW1haWwiOiJkYW1vbkBjZXByby5jby51ayIsInBlcm1pc3Npb25zIjpbImNvcmUuY2FuX2FjY2Vzc19jb3JvbmEiLCJjb3JlLmNhbl9hY2Nlc3Nfb3dsX2RhdGEiLCJjb3JlLmNhbl9hY2Nlc3NfcGhvZW5peCIsImNvcmUuY2FuX2FjY2Vzc192cHBfZGF0YSJdLCJsZWdhY3lfaWQiOm51bGwsImV4cCI6MTY0OTQ2NzUyOX0.hVO-7YjnGnWN53_tqv4vHw0NN3yafIY5y8ua4PeytJ0"}

    # Set the params
    params = {
        'start_date': date_from,
        'end_date': date_to,
        'granularity': granularity
    }

    # Fetch the APX pricing from midnight to midnight (remember, last time period is 23:30-00:00)
    response = requests.get("https://api.limejump.com/api/2.0/analytics/market_prices", params=params, headers=headers)
    if response.status_code == 200:
        # Interpret the text payload in the response, and return the query result
        response = json.loads(response.text)['result']
    else:
        raise Exception("Not authorised by Limejump (have you checked the Auth token?)")

    APXPrice = []
    for timeslot in response:
        # Parse the UTC string to a datetime object
        # Can't do Timezone with colon, so this is the easiest option
        # Yes, I can do *better*, but that's not the point
        timeslot[0] = datetime.datetime.strptime(timeslot[0][0:19], '%Y-%m-%dT%H:%M:%S')
        # If the time is in the future (because it gives you the whole of every day you ask about)
        #   put it on the list
        if date_from <= timeslot[0] <= date_to:
            APXPrice.append(timeslot)

    return APXPrice

# Reusing the APX code to get the SSP as well, watch out, not dividing by 10
def SSPasList(date_from, date_to):
    # T: NOT dividing by ten, keeping the GBP/MWh!
    # Get SSP pricing for the next 24hrs
    SSP = getSSP(date_from, date_to)

    pricing = []
    for timeslot in SSP:
        pricing.append(timeslot[1])
    return pricing

def getSSP(date_from, date_to, granularity='hh'):
    import requests
    import json

    # Set the headers (Auth token), last update 27/3
    headers = {
        "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MTI5NCwiZW1haWwiOiJkYW1vbkBjZXByby5jby51ayIsInBlcm1pc3Npb25zIjpbImNvcmUuY2FuX2FjY2Vzc19jb3JvbmEiLCJjb3JlLmNhbl9hY2Nlc3Nfb3dsX2RhdGEiLCJjb3JlLmNhbl9hY2Nlc3NfcGhvZW5peCIsImNvcmUuY2FuX2FjY2Vzc192cHBfZGF0YSJdLCJsZWdhY3lfaWQiOm51bGwsImV4cCI6MTY0OTQ2NzUyOX0.hVO-7YjnGnWN53_tqv4vHw0NN3yafIY5y8ua4PeytJ0"}

    # Set the params
    params = {
        'start_date': date_from,
        'end_date': date_to,
        'granularity': granularity
    }

    # Fetch the SSP pricing from midnight to midnight (remember, last time period is 23:30-00:00)
    response = requests.get("https://api.limejump.com/api/2.0/analytics/system_prices", params=params, headers=headers)
    if response.status_code == 200:
        # Interpret the text payload in the response, and return the query result
        response = json.loads(response.text)['result']
    else:
        raise Exception("Not authorised by Limejump (have you checked the Auth token?)")

    SSPPrice = []
    for timeslot in response:
        # Parse the UTC string to a datetime object
        # Can't do Timezone with colon, so this is the easiest option
        # Yes, I can do *better*, but that's not the point
        timeslot[0] = datetime.datetime.strptime(timeslot[0][0:19], '%Y-%m-%dT%H:%M:%S')
        # If the time is in the future (because it gives you the whole of every day you ask about)
        #   put it on the list
        if date_from <= timeslot[0] <= date_to:
            SSPPrice.append(timeslot)

    return SSPPrice

if __name__ == "__main__":
    # Grab the APX data for the next 24hrs OR not
    # response = getAPX(datetime.datetime.now() - datetime.timedelta(days=1), datetime.datetime.now() - datetime.timedelta(days=0))
    # print(response)
    # response = APXasList(datetime.datetime.now() - datetime.timedelta(days=1), datetime.datetime.now() - datetime.timedelta(days=0))
    # print(response)

    response = getSSP(datetime.datetime.now() - datetime.timedelta(days=1),
                      datetime.datetime.now() + datetime.timedelta(days=1))
    print(response)
    response = SSPasList(datetime.datetime.now() - datetime.timedelta(days=1),
                         datetime.datetime.now() + datetime.timedelta(days=1))
    print(response)
