def completedObjToCSV(completed_parsed):
    # Single-day optimisation
    # T: adding grid emissions and battery, Mixergy not differentiating self-consumption & import anymore
    system = completed_parsed['system']
    solution = completed_parsed['solution']
    csv_data = []
    # Define the column headers
    firstrow = ['I', 'paidI', 'X', 'paidX', 'G', 'E', 'Real Exp', 'Real Imp', 'Sim Exp', 'Sim Imp', 'P-ECC', 'P-Nursery', 'Batt Imp', 'Batt Exp(neg)']
    for tank in system['tanks']:
        firstrow.append(tank + '_H')
        firstrow.append(tank + '_E')

    csv_data.append(firstrow)
    # Pull the data out, as all arrays must be the same length
    for t in range(solution['max_time']+1):
        thisrow = [system['I'][t], system['paidI'][t], system['X'][t], system['paidX'][t], system['G'][t], system['E'][t], system['SM']['EXP'][t], system['SM']['IMP'][t]]
        # Make sure we include every one of n tanks
        # H was part of the problem set
        # e, m, z, y, p are the solution

        # for power in solution:
        thisrow.extend([

            solution['e'][t],
            solution['m'][t],
            solution['pECC'][t],
            solution['pNursery'][t],
            solution['z'][t],
            solution['y'][t]
        ])
        for tank in system['tanks']:
            thisrow.extend([
                system['tanks'][tank].H(t),
                system['tanks'][tank].realworldE(t),

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
    from optimizer import DHWOptimizer
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
    from utilities import recursiveReplace
    output_filename = './output/210916-Batt-Mix-vs.csv'
    # Load the config to a JSON dict
    configfile = './input_data/systemconfig-v5.json'
    config = loadFromJSON(configfile)

    # Set all dates in Config file to a new one; comment out if needed to use different dates for different datasets
    up_date_from = "2021-09-16T00:00:00"
    up_config = recursiveReplace(config, "date_from", up_date_from)

    completed_parsed = main(up_config)
    data_as_csv = completedObjToCSV(completed_parsed)
    
    # Save as csv for everyone's use
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
    # for tank in tanks:
        # completed_parsed['system']['tanks'][tank] = {"H": tanks[tank].H()}

    # T: override the previous file to write it as JSON to a .CSV file, because why not
    # saveAsJSON(output_filename, completed_parsed)
