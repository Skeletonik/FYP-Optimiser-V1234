def loadFromJSON (filename):
    import json
    with open(filename, 'r') as infile:
        return json.load(infile)

def saveAsJSON (filename, data):
    import json
    with open(filename, 'w') as outfile:
        json.dump(data, outfile)

def parseOptimizer (lp_solution):
    variables = lp_solution['lp_variables']
    powers = {"i":{}, "s":{}}
    max_time = 0
    for variable in variables:
        # Variables auto-named by PuLP in format:
        #  [current_source][tank]_[timeslot]
        # So this makes a list ["[current_source][tank]", "[timeslot]"]
        name_components = variable.name.split('_')
        # Separate this out to easier to read names
        current_source = name_components[0][0]
        tank = name_components[0][1:]
        time = int(name_components[1])
        # Take the value of the variable object
        # We have to name a slot in the dict after it because order of input is 0, 1, 10...
        # Fix it below
        if tank not in powers[current_source]:
            powers[current_source][tank] = {}
        powers[current_source][tank][time] = variable.varValue
        max_time = max(max_time, time)

    # Invert the structure, from tanks per power to powers per tank
    new_powers = {}
    for tank in powers[current_source]:
        new_powers[tank] = {}
        new_powers[tank]['i'] = [powers['i'][tank][t] for t in range(max_time)]
        new_powers[tank]['s'] = [powers['s'][tank][t] for t in range(max_time)]
    return new_powers



if __name__ == "__main__":
    
    response = loadFromJSON('systemconfig.json')
    print(response)