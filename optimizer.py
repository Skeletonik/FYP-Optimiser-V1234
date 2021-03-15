### ECC DHW OPTIMISER
### RELEASE 0.0a
### Functionality: Import

def main(system:object) -> object:
    """ LINEAR OPTIMIZER Rev 0.1a
    Uses I and H to produce power plan for a single tank
    Supports system: I, X, G, H, heater_power, l_per_kWh, W_init, loss, dilution
    """

    # VALIDATION
    for tank in system['tanks']:
        # Validate config
        if not (system['tanks'][tank]['heater_power'] > 0 and system['tanks'][tank]['litres_per_kWh'] > 0 and system['tanks'][tank]['dilution'] >= 1 and
                0 <= system['tanks'][tank]['loss'] <= 1 and system['tanks'][tank]['w_init'] >= 0):
            return {'status': 1, 'error':"Invalid configuration" + tank['name']}
        
    # Validate system description
        # Validate that all(lengths of each H for each tank in the system) == other lengths
    if (len(system['I']) == len(system['X']) == len(system['G']) and 
            all([len(this_H) == len(system['I']) for this_H in [system['tanks'][tank]['H'] for tank in system['tanks']]])):
        timeslots = range(len(system['I']))
    else:
        return {'status': 1, 'error':"Mismatched param lengths"}

    # LINEAR PROGRAMMING SETUP
    # Import PuLP (Linear Programming)
    import pulp

    # Define the problem as (cost) minimisation
    prob = pulp.LpProblem("Water Optimisation", pulp.LpMinimize)

    # VARIABLES
    # There are as many of them as there are tanks*time slots, they must be >=0 and are continuous
    # i = import_power
    # s = self-consumed power
    # x is implicit, and is G[t] - sum(s[t])
    # Calculate self-consumption to stop system trying to re-export imported 
    #   power when export > import
    i = {}
    s = {}
    for tank in system['tanks']:
        i[tank] = pulp.LpVariable.dicts("i"+tank, [n for n in timeslots], lowBound=0, cat='Continuous')
        s[tank] = pulp.LpVariable.dicts("s"+tank, [n for n in timeslots], lowBound=0, cat='Continuous')

    # OBJECTIVE
    # Sum of ([import costs] - [export costs])
    prob += pulp.lpSum([system['I'][t]*i[tank][t] - system['X'][t]*(system['G'][t]-s[tank][t]) for t in timeslots for tank in system['tanks']])      

    # CONSTRAINTS
    w = {}
    x = []
    for t in timeslots:
        # For every tank in the system. All EQs in here apply to each tanks
        for tank in system['tanks']:
            if t == 0:
                # Create a w[ater level] list for each tank
                w[tank] = []
                # If this is the first time slot, set the water level to the w_init
                w[tank].append(system['tanks'][tank]['w_init'])
            else:
                # Otherwise, calculate water from the previous 30min and consumption/generation
                # water at t is (w[t-1] - consumption)*(1-loss) + heated volume
                w[tank].append(
                    (w[tank][t-1] - system['tanks'][tank]['H'][t-1]*system['tanks'][tank]['dilution'])*(1-system['tanks'][tank]['loss']) + 
                    (i[tank][t-1]+s[tank][t-1])*system['tanks'][tank]['litres_per_kWh']
                )
            # Ensure available DHW at t in each tank >= DHW demand (after dilution) in coming 30min (i.e. demand is met)
            prob  += w[tank][t] >= system['tanks'][tank]['H'][t]*system['tanks'][tank]['dilution']
            # Heater power limited
            prob  += i[tank][t]+s[tank][t] <= system['tanks'][tank]['heater_power']
            # Each tank has a capacity limit
            prob += 0 <= w[tank][t] <= system['tanks'][tank]['tank_capacity']
            
        # Can only use generated solar once across all tanks
        prob += pulp.lpSum([s[tank][t] for tank in system['tanks']]) <= system['G'][t]
        

    # LINEAR PROGRAMMING SOLUTION
    # CBC is the default, but needs defining so I can set msg=0
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    # prob.solve()

    # PACKAGE RETURN OBJECT
    feedback = {}
    feedback['lp_status']    = pulp.LpStatus[prob.status]
    # Status 0 means things went well. Status 2 means optimization failed
    feedback['status']       = 0 if feedback['lp_status'] == "Optimal" else 2
    feedback['lp_variables'] = prob.variables()
    feedback['cost']         = pulp.value(prob.objective)
    return feedback