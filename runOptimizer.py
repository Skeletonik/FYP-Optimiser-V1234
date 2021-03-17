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
    """ RUNOPTIMIZER MAIN() v2
        Now with dramatic code quality improvements!
        
        """
    # Import
    from utilities import loadFromJSON
    from utilities import datetimeify
    from optimizer import DHWOptimizer
    import time ############################################################################

    # Load the config to a JSON object
    config = loadFromJSON(configfile)

    # ASSEMBLE SYSTEM
    # Fortunately there's a fancy new class for that
    from SystemAssembler import SystemAssembler
    SA = SystemAssembler(config)
    SA.autoFill()
    system = SA.system()

    # SOLVE THE SYSTEM
    # Fortunately there's also a class for that
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
        # lp_parsed = parseOptimizer(lp.result())    
        lp_parsed = lp.asObj()
        response['solution'] = lp_parsed
    # If param lengths were mismatched
    elif lp.result('status') == 1:
        Exception("ERROR: Mismathced param lengths: ", lp.result())
    # If solution was sub-optimal
    elif lp.result('status') == 2:
        print("Sub-optimal")
    else:
        Exception("Something broke. Send help")
    
    return response


if __name__ == "__main__":
    import csv
    from utilities import saveAsJSON
    completed_parsed = main('./input_data/systemconfig-v2.json')
    data_as_csv = completedObjToCSV(completed_parsed)
    
    # Save as csv for Damon's use
    with open('./output/completedoptimizer-realdata.csv', 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for row in data_as_csv:
            writer.writerow(row)

    # Also save it as a JSON object
    saveAsJSON('./output/completedoptimizer-realdata.json', completed_parsed)
