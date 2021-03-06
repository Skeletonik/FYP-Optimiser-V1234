def completedObjToCSV(completed_parsed):
    # T: adding grid emissions only
    system = completed_parsed['system']
    solution = completed_parsed['solution']
    csv_data = []
    # Define the column headers
    firstrow = ['I', 'paidI', 'X', 'paidX', 'G', 'E']
    for tank in system['tanks']:
        firstrow.append(tank + '_H')
        firstrow.append(tank + '_E')
        firstrow.append(tank + '_i')
        firstrow.append(tank + '_s')
    csv_data.append(firstrow)
    # Pull the data out, as all arrays must be the same length
    for t in range(solution['max_time']+1):
        thisrow = [system['I'][t], system['paidI'][t], system['X'][t], system['paidX'][t], system['G'][t], system['E'][t]]
        # Make sure we include every one of n tanks
        # H was part of the problem set
        # i and s are the solution
        for tank in system['tanks']:
            thisrow.extend([
                system['tanks'][tank].H(t), 
                system['tanks'][tank].realworldE(t), 
                solution[tank]['i'][t], 
                solution[tank]['s'][t]
            ])
        csv_data.append(thisrow)

    return csv_data
        
def main(config:dict):
    """ RUNOPTIMIZER MAIN() v2
        Now with dramatic code quality improvements!

        """
    # Import
    from utilities import datetimeify
    from SystemAssembler import SystemAssembler
    from optimizerV12 import DHWOptimizer
    import time ############################################################################

    # ASSEMBLE SYSTEM
    # Fortunately there's a fancy new class for that
    SA = SystemAssembler(config)
    SA.autoFill()
    system = SA.system()

    # SOLVE THE SYSTEM
    # Fortunately there's also a class for that
    print("Begin LP solution")
    tic = time.perf_counter()
    lp = DHWOptimizer(system)
    toc = time.perf_counter()
    print("LP took ", toc-tic, " seconds")

    # Create dict which contains the system which was run,
    #   and the response, if appropriate
    response = {
        "lp_duration": toc-tic,
        "system": system
    }

    # If the optimizer succeeded
    if lp.result('status') == 0: 
        response['solution'] = lp.asDict()
    # If param lengths were mismatched
    elif lp.result('status') == 1:
        raise Exception("ERROR: Mismatched param lengths: ", lp.result())
        
    # If solution was sub-optimal
    elif lp.result('status') == 2:
        print("Sub-optimal")
    else:
        raise Exception("Something broke. Send help")
    
    return response


if __name__ == "__main__":
    import csv
    from utilities import saveAsJSON
    from utilities import loadFromJSON
    output_filename = './output/21-09-16_2mix_0CP-V2.csv'
    # Load the config to a JSON dict
    configfile = './input_data/systemconfig-v5.json'
    config = loadFromJSON(configfile)
    completed_parsed = main(config)
    data_as_csv = completedObjToCSV(completed_parsed)
    
    # Save as csv for Damon's use
    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for row in data_as_csv:
            writer.writerow(row)

    # Also save it as a JSON dict
    # Temporarily remove the tanks, because they're now objects
    tanks = completed_parsed['system']['tanks']
    # Just pull the H lists for each tank
    # Objects aren't serialisable
    # That's the bulk, but not entirety, of useful output
    for tank in tanks:
        completed_parsed['system']['tanks'][tank] = {"H": tanks[tank].H()}

    # T: override the previous file to write it as JSON to a .CSV file, because why not
    # saveAsJSON(output_filename, completed_parsed)
