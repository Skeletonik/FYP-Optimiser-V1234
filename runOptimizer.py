def parseOptimizer (lp_solution):
    variables = lp_solution['lp_variables']
    powers = {"i":{}, "s":{}}
    max_time = 0
    for variable in variables:
        # Variables auto-named by PuLP in format: [current_source][tank]_[timeslot]
        # So this makes a list ["[current_source][tank]", "[timeslot]"] for this variable
        name_components = variable.name.split('_')
        # Separate the name out to its component parts
        current_source = name_components[0][0]
        tank = name_components[0][1:]
        time = int(name_components[1])
        
        if tank not in powers[current_source]:
            powers[current_source][tank] = {}
        # Take the value of the variable object
        # Because the order of [variables] is 0, 1, 10, 11, etc. we have to make a dict
        # The dict has to be created with current source as the highest level, because we know beforehand
        #   only i and s are possible options. Then, we can create all the tanks as we work our way through
        # Couldn't think of a way to go directly to a powers[tank][current_source][time] structure
        # Maybe I'm just tired. 
        # Fix it below
        powers[current_source][tank][time] = variable.varValue
        max_time = max(max_time, time)

    # Invert the structure, from tanks per power to powers per tank
    new_powers = {"max_time": max_time}
    for tank in powers[current_source]:
        new_powers[tank] = {}
        new_powers[tank]['i'] = [powers['i'][tank][t] for t in range(max_time+1)]
        new_powers[tank]['s'] = [powers['s'][tank][t] for t in range(max_time+1)]
    return new_powers

def completedObjToCSV(completed_parsed):
    system = completed_parsed['system']
    solution = completed_parsed['solution']
    csv_data = []
    # Define the column headers
    firstrow = ['I', 'X', 'G']
    for tank in system['tanks']:
        firstrow.append(tank + '_H')
        firstrow.append(tank + '_i')
        firstrow.append(tank + '_s')
    csv_data.append(firstrow)
    # Pull the data out, as all arrays must be the same length
    for t in range(solution['max_time']+1):
        thisrow = [system['I'][t], system['X'][t], system['G'][t]]
        # Make sure we include every one of n tanks
        # H was part of the problem set
        # i and s are the solution
        for tank in system['tanks']:
            thisrow.extend([system['tanks'][tank]['H'][t], solution[tank]['i'][t], solution[tank]['s'][t]])
        csv_data.append(thisrow)

    return csv_data
        
def main(configfile):
    # Import
    from utilities import loadFromJSON
    from utilities import datetimeify
    from optimizer import DHWOptimizer
    import time ############################################################################

    # Load the config to a JSON object
    config = loadFromJSON(configfile)

    # Create empty system object to pass to optimizer
    system = {}
    # Check the sources of every variable system variable
    # I, X, G, tanks
    for var_name in config['dataSources']:
        if config['dataSources'][var_name]['source'] == "included":
            system[var_name] = config[var_name]
        elif config['dataSources'][var_name]['source'] == "JSON":
            system[var_name] = loadFromJSON(config['dataSources'][var_name]['filename'])[var_name]
        elif config['dataSources'][var_name]['source'] == "limejump":
            ## Currently not working
            # LJ provide 24hrs data, 00:00-00:00 (49 points hh-ly)
            # So need to trim that
            # Also, need to align if we're not running from midnight
            from fetchLJ import lj_rest
            # from datetime import datetime # LJ only do whole days
            # date_from = datetime.strptime(config['dataSources'][var_name]['date_from'], "%Y-%m-%d")
            # date_to = datetime.strptime(config['dataSources'][var_name]['date_to'], "%Y-%m-%d")
            date_from = datetimeify(config['dataSources'][var_name]['date_from'])
            date_to = datetimeify(config['dataSources'][var_name]['date_to'])
            # grab the APX data, divide by 10 for p/kWh
            # getAPX provides {date, price (£/MWh)}
            system[var_name] = [ 
                x[1]/10 for x in 
                    lj_rest.getAPX(
                            date_from, 
                            date_to
                        ) if (date_from <= x[0] < date_to)
                ]
        elif config['dataSources'][var_name]['source'] == "LJ_CSV":
            # sledgehammer, walnut, we meet again
            import os, sys
            sys.path.append(os.path.relpath('./fetchLJ'))
            # pylint: disable=import-error
            from datetime import datetime
            from LJfromCSV import main as LJfromCSV
            # Yes, this will run twice. There ought to be some way to deal with that... TBD
            system[var_name] = LJfromCSV(
                config['dataSources'][var_name]['filename'], 
                datetimeify(config['dataSources'][var_name]['date_from']), 
                datetimeify(config['dataSources'][var_name]['date_to'])
            )[var_name]
        elif config['dataSources'][var_name]['source'] == "PV_CSV":
            # sledgehammer, walnut, we meet again
            import os, sys
            sys.path.append(os.path.relpath('./fetchPV'))
            # pylint: disable=import-error
            from datetime import datetime
            from PVfromCSV import main as PVfromCSV
            system[var_name] = PVfromCSV(
                config['dataSources'][var_name]['filename'], 
                datetimeify(config['dataSources'][var_name]['date_from']), 
                datetimeify(config['dataSources'][var_name]['date_to'])
            )

    # check the sources of every tank's H[ot water demand]
    for tank in system['tanks']:
        if system['tanks'][tank]['H']['source'] == 'included':
            system['tanks'][tank]['H'] = system['tanks'][tank]['H']['timeseries']
        elif system['tanks'][tank]['H']['source'] == 'JSON':
            system['tanks'][tank]['H'] = loadFromJSON(system['tanks'][tank]['H']['filename'])['H']

    # ### TBD ####
    # ### Really janky, but it works ####
    # extend_times = 184
    # for tank in system['tanks']:
    #     system['tanks'][tank]['H'] = system['tanks'][tank]['H']*extend_times ############################################################################
    # system['G'] = system['G']*extend_times

    print("Begin LP solution")
    tic = time.perf_counter()
    lp = DHWOptimizer(system)
    toc = time.perf_counter()
    print("That took ", toc-tic, " seconds")

    response = {
        "system": system
    }

    # If the optimizer succeeded
    if lp.result('status') == 0:
        lp_parsed = parseOptimizer(lp.result())    
        response['solution'] = lp_parsed
    # If param lengths were mismatched
    elif lp.result('status') == 1:
        print("ERROR: ", lp.result())
    # If solution was sub-optimal
    elif lp.result('status') == 2:
        print("Sub-optimal")
    else:
        print("Something broke. Send help")
    
    return response


if __name__ == "__main__":
    import csv
    from utilities import saveAsJSON
    completed_parsed = main('./input_data/systemconfig.json')
    data_as_csv = completedObjToCSV(completed_parsed)
    
    # Save as csv for Damon's use
    with open('./output/completedoptimizer-realdata.csv', 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for row in data_as_csv:
            writer.writerow(row)

    # Also save it as a JSON object
    saveAsJSON('./output/completedoptimizer-realdata.json', completed_parsed)
