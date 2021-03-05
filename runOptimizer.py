def main(configfile):
    # Import
    from utilities import loadFromJSON
    from utilities import parseOptimizer
    from optimizer import main as optimizer

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
            from datetime import datetime # LJ only do whole days
            date_from = datetime.strptime(config['dataSources'][var_name]['date_from'], "%Y-%m-%d")
            date_to = datetime.strptime(config['dataSources'][var_name]['date_to'], "%Y-%m-%d")
            system[var_name] = [x[1]/10 for x in lj_rest.getAPX(date_from, date_to) if (date_from <= x[0] < date_to)]

    # check the sources of every tank's H[ot water demand]
    for tank in system['tanks']:
        if system['tanks'][tank]['H']['source'] == 'included':
            system['tanks'][tank]['H'] = system[tank]['H']['timeseries']
        elif system['tanks'][tank]['H']['source'] == 'JSON':
            system['tanks'][tank]['H'] = loadFromJSON(system['tanks'][tank]['H']['filename'])['H']

    lp_solution = optimizer(system)
    print(lp_solution)

    if lp_solution['status'] == 0:
        lp_parsed = parseOptimizer(lp_solution)
    
    return {
        "system": system,
        "solution": lp_parsed
    }

if __name__ == "__main__":
    from utilities import saveAsJSON
    completed_parsed = main('./input_data/systemconfig.json')
    saveAsJSON('completedoptimizer.json', completed_parsed)
